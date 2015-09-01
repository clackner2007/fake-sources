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


def polyReadWkb(wkbName, load=True):

    wkbFile = open(wkbName, 'r')
    polyWkb = wkbFile.read().decode('hex')
    wkbFile.close()

    if load is True:
        return wkb.loads(polyWkb)
    else:
        return polyWkb


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
                              optional=True, default=None)
    rejMask = pexConfig.Field(doc='region to mask out',
                              dtype=str,
                              optional=True, default=None)

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
        raArr, decArr = np.array(zip(*makeRaDecCat.getRandomRaDec(nFakes,
                                                            ra_vert[0].asDegrees(),
                                                            ra_vert[-1].asDegrees(),
                                                            dec_vert[0].asDegrees(),
                                                            dec_vert[-1].asDegrees(),
                                                            rad=self.config.rad)))
        """
        Added by Song Huang 2016-09-01
        Filter the random RA, DEC using two filters
        """
        if self.config.acpMask is not None or self.config.rejMask is not None:
            try:
                from shapely import wkb
                from shapely.geometry import Point
            except ImportError:
                raise Exception('Please install the Shapely library before using this function')

            if os.path.isfile(self.config.acpMask):
                acpRegs = polyReadWkb(self.config.acpMask)
                inside = map(lambda x, y: acpRegs.contains(Point(x, y)), raArr, decArr)
            else:
                inside = np.isfinite(raArr)

            if os.path.isfile(self.config.rejMask):
                regRegs = polyReadWkb(self.config.rejMask)
                masked = map(lambda x, y: rejRegs.contains(Point(x, y)), raArr, decArr)
            else:
                masked = np.isnan(raArr)

            useful = map(lambda x, y: x and (not y), inside, masked)
            ra, dec = raArr[useful], decArr[useful]
        else:
            ra, dec = raArr, decArr

        outTab = astropy.table.Table()
        outTab.add_column(astropy.table.Column(name="RA", data=ra))
        outTab.add_column(astropy.table.Column(name="Dec", data=dec))
        if self.config.inputCat is not None:
            galData = astropy.table.Table().read(self.config.inputCat)
            randInd = np.random.choice(range(len(galData)), size=nFakes)
            mergedData = galData[randInd]
            for colname in mergedData.columns:
                outTab.add_column(astropy.table.Column(name=colname,
                                                       data=mergedData[colname]))

        outTab.write(os.path.join(self.config.outDir,
                                  'src_%d_radec.fits'%tractId),
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
