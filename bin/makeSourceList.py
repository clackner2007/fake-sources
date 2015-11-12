#!/usr/bin/env python
"""
make a source catalog of galaxies, possibly with shear
"""
import os
import numpy as np
import lsst.pipe.base      as pipeBase
import lsst.pipe.tasks.coaddBase as coaddBase
import lsst.pex.config     as pexConfig
import lsst.afw.image      as afwImage
import lsst.afw.cameraGeom as camGeom
import astropy.table
import fakes.makeRaDecCat as makeRaDecCat


class MakeFakeInputsConfig(pexConfig.Config):
    coaddName = pexConfig.ChoiceField(
        dtype   = str,
        doc     = "Type of data to use",
        default = "deep",
        allowed = {"deep"   : "deepCoadd"}
        )
    rhoFakes = pexConfig.Field(doc="number of fakes per patch", dtype=int,
                               optional=False, default=500)
    inputCat = pexConfig.Field(
        doc="input galaxy catalog, if none just return ra/dec list",
        dtype=str,
        optional=True, default=None)
    outDir = pexConfig.Field(doc='output directory for catalogs',
                             dtype=str,
                             optional=True, default='.')
    rad = pexConfig.Field(doc="minimum distance between fake objects", dtype=float,
                               optional=True, default=None)
    acpMask = pexConfig.Field(doc='region to include',
                              dtype=str,
                              optional=True, default='')
    rejMask = pexConfig.Field(doc='region to mask out',
                              dtype=str,
                              optional=True, default='')
    innerTract = pexConfig.Field(doc='only add to the inner Tract region or not',
                              dtype=bool,
                              optional=True, default=False)
    uniqueID = pexConfig.Field(doc='Use the index as unique ID of the fake object',
                              dtype=bool,
                              optional=True, default=True)

class MakeFakeInputsTask(pipeBase.CmdLineTask):
    """a task to make an input catalog of fake sources for a dataId"""

    _DefaultName='makeFakeInputs'
    ConfigClass = MakeFakeInputsConfig

    def run(self, dataRef):
        print dataRef.dataId
        skyMap = dataRef.get('deepCoadd_skyMap', immediate=True)
        tractId = dataRef.dataId['tract']
        tract = skyMap[tractId]
        extPatch = tract.getNumPatches()
        nPatch = extPatch.getX() * extPatch.getY()
        nFakes = self.config.rhoFakes * nPatch
        ra_vert, dec_vert = zip(*tract.getVertexList())
        ra_vert = sorted(ra_vert)
        dec_vert = sorted(dec_vert)
        ra0 = ra_vert[0].asDegrees()
        ra1 = ra_vert[-1].asDegrees()
        dec0 = dec_vert[0].asDegrees()
        dec1 = dec_vert[-1].asDegrees()

        """
        Added by Song Huang 2016-09-02
        Tracts in the Deep and Wide layers are defined to have overlaps of 1 arcmin
        between the two adjacent Tracts: 1 arcmin ~ 0.01667 deg
        """
        if self.config.innerTract:
            ra0 += 0.0167
            ra1 -= 0.0167
            dec0 += 0.0167
            dec1 -= 0.0167

        raArr, decArr = np.array(zip(*makeRaDecCat.getRandomRaDec(nFakes, ra0, ra1,
                                                                  dec0, dec1,
                                                                  rad=self.config.rad)))
        """
        Added by Song Huang 2016-09-01
        Filter the random RA, DEC using two filters
        """
        if (self.config.acpMask != '') or (self.config.rejMask != ''):
            try:
                from shapely import wkb
                from shapely.geometry import Point
            except ImportError:
                raise Exception('Please install the Shapely library before using this function')

            if (self.config.acpMask != '') and os.path.isfile(self.config.acpMask):
                print "## Filter through : %s" % self.config.acpMask
                acpWkb = open(self.config.acpMask, 'r')
                acpRegs = wkb.loads(acpWkb.read().decode('hex'))
                acpWkb.close()
                inside = np.asarray(map(lambda x, y: acpRegs.contains(Point(x, y)),
                                    raArr, decArr))
            else:
                inside = np.isfinite(raArr)

            if (self.config.rejMask != '') and os.path.isfile(self.config.rejMask):
                print "## Filter through : %s" % self.config.rejMask
                rejWkb = open(self.config.rejMask, 'r')
                rejRegs = wkb.loads(rejWkb.read().decode('hex'))
                rejWkb.close()
                masked = np.asarray(map(lambda x, y: rejRegs.contains(Point(x, y)),
                                    raArr, decArr))
            else:
                masked = np.isnan(raArr)

            useful = np.asarray(map(lambda x, y: x and (not y), inside, masked))
            ra, dec = raArr[useful], decArr[useful]

            print "## %d out of %d objects left" % (len(ra), len(raArr))
            nFakes = len(ra)
        else:
            ra, dec = raArr, decArr

        outTab = astropy.table.Table()

        """ Song Huang
        Rename the input ID to modelID; and use the index as ID
        """
        outTab.add_column(astropy.table.Column(name="RA", data=ra))
        outTab.add_column(astropy.table.Column(name="Dec", data=dec))
        if self.config.inputCat is not None:
            galData = astropy.table.Table().read(self.config.inputCat)
            randInd = np.random.choice(range(len(galData)), size=nFakes)
            mergedData = galData[randInd]

            for colname in mergedData.columns:
                outTab.add_column(astropy.table.Column(name=colname,
                                                   data=mergedData[colname]))

            if ('ID' in outTab.colnames) and (self.config.uniqueID):
                print "## Rename the ID column"
                outTab.rename_column('ID', 'modelID')
                outTab.add_column(astropy.table.Column(name="ID",
                    data=np.arange(len(outTab))))

            """ Modified by SH; to generate multiBand catalog at the same time"""
            magList = [col for col in galData.colnames if 'mag_' in col]
            if len(magList) >= 1:
                print "Find magnitude in %d band(s)"%len(magList)
                for mag in magList:
                    try:
                        outTab.remove_column('mag')
                    except KeyError:
                        pass
                    outTab.add_column(astropy.table.Column(name='mag',
                                                        data=mergedData[mag]))
                    outFits = os.path.join(self.config.outDir,
                            'src_%d_radec_%s.fits'%(tractId, mag.split('_')[1].upper()))
                    print outFits
                    outTab.write(outFits, overwrite=True)
            else:
                outTab.write(os.path.join(self.config.outDir,
                                          'src_%d_radec.fits'%tractId),
                             overwrite=True)
        else:
            outTab.write(os.path.join(self.config.outDir,
                                      'src_%d_radec_only.fits'%tractId),
                         overwrite=True)


    @classmethod
    def _makeArgumentParser(cls, *args, **kwargs):
        parser = pipeBase.ArgumentParser(name="makeFakeInputs", *args, **kwargs)
        parser.add_id_argument("--id", datasetType="deepCoadd",
                               help="data ID, e.g. --id tract=0",
                               ContainerClass=coaddBase.CoaddDataIdContainer)

        return parser

    # Don't forget to overload these
    def _getConfigName(self):
        return None
    def _getEupsVersionsName(self):
        return None
    def _getMetadataName(self):
        return None

if __name__=='__main__':
    MakeFakeInputsTask.parseAndRun()
