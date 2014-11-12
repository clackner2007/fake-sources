#!/usr/bin/env python
"""
matchFakes.py
matches fakes based on position stored in the calibrated exposure image header
"""

import lsst.daf.persistence as dafPersist
from lsst.afw.table import SourceCatalog, SchemaMapper
import lsst.pex.exceptions
import numpy as np
import argparse
import re
import collections
import astropy.table
import lsst.afw.geom.ellipses

def getEllipse(quad):
    """
    returns the semi-major axis, axes ratio and PA for a given quadrupole moment
    """
    e = lsst.afw.geom.ellipses.Axes(quad)
    return e.getA(), e.getB()/e.getA(), e.getTheta() * 180.0/np.pi


def getFakeSources(butler, dataId, tol=1.0, zeropoint=True,
                   visit=False, ccd=False):
    """Get list of sources which agree in position with fake ones with tol
    """
    
    sources = butler.get('src', dataId)
    cal_md = butler.get('calexp_md', dataId)
    if zeropoint:
        zp = 2.5*np.log10(cal_md.get('FLUXMAG0'))

    fakeXY = collections.defaultdict(tuple)
    fakename = re.compile('FAKE([0-9]+)')
    for card in cal_md.names():
        m = fakename.match(card)
        if m is not None:
            x,y = map(float, (cal_md.get(card)).split(','))
            fakeXY[int(m.group(1))] = (x,y)


    srcX, srcY = sources.getX(), sources.getY()
    srcIndex = collections.defaultdict(list)
    for fid, fcoord  in fakeXY.items():
        matched = ((np.abs(srcX-fcoord[0]) < tol) & 
                   (np.abs(srcY-fcoord[1]) < tol))
        s1 = sources.subset(matched)
        srcIndex[fid] = np.where(matched)[0]


    mapper = SchemaMapper(sources.schema)
    mapper.addMinimalSchema(sources.schema)
    newSchema = mapper.getOutputSchema()
    newSchema.addField('fakeId', type=int, doc='id of fake source matched to position')
    if zeropoint:
        newSchema.addField('zeropoint', type=float, doc='magnitude zeropoint')
    if visit:
        newSchema.addField('visit', type=float, doc='visit id')
    if ccd:
        newSchema.addField('ccd', type=float, doc='ccd id')
    srcList = SourceCatalog(newSchema)
    srcList.reserve(sum([len(s) for s in srcIndex.values()]))

    for ident, sindlist in srcIndex.items():
        for ss in sindlist:
            newRec = srcList.addNew()
            newRec.assign(sources[ss], mapper)
            newRec.set('fakeId', ident)
            if zeropoint:
                newRec.set('zeropoint', zp)
            if visit:
                newRec.set('visit', dataId['visit'])
            if ccd:
                newRec.set('ccd', dataId['ccd'])

    return srcList


def getAstroTable(srcIn, mags=True):
    """
    returns an astropy table with all the src entries
    if the entries are complex objects, it breaks them down
    
    if mags is True, returns the magnitudes for all the flux columns
    (not implemented yet)
    """
    
    tab = astropy.table.Table()
    src = srcIn.copy()
    for name in src.schema.getNames():
        try: 
            tab.add_column(astropy.table.Column(name=name,
                                                data=src.get(name)))
        except lsst.pex.exceptions.LsstException:
            if type(src[0].get(name)) is lsst.afw.geom.ellipses.ellipsesLib.Quadrupole:
                reff, q, theta = zip(*[getEllipse(s.get(name)) for s in src])
                tab.add_column(astropy.table.Column(name=name+'_a', data=reff))
                tab.add_column(astropy.table.Column(name=name+'_q', data=q))
                tab.add_column(astropy.table.Column(name=name+'_theta', data=theta))
            elif type(src[0].get(name)) is lsst.afw.coord.coordLib.IcrsCoord:
                x, y= zip(*[(s.get(name).getRa().asDegrees(), 
                             s.get(name).getDec().asDegrees()) for s in src])
                tab.add_column(astropy.table.Column(name=name+'_ra', data=x))
                tab.add_column(astropy.table.Column(name=name+'_dec', data=y))
            else:
                tab.add_column(astropy.table.Column(name=name, 
                                                    data=np.array([s.get(name) for s in src])))



    return tab



def main():

    #TODO: this should use the LSST/HSC conventions
    parser = argparse.ArgumentParser()
    parser.add_argument('rootDir', help='root dir of data repo')
    parser.add_argument('visit', help='id of visit', type=int)
    parser.add_argument('ccd', help='id of ccd', type=int)
    args = parser.parse_args()
    
    butler = dafPersist.Butler(args.rootDir)

    slist = getFakeSources(butler,
                                 {'visit':args.visit, 'ccd':args.ccd})

    print 'fakeId X Y cmodel_mag nChild kron_mag'
    for s in slist:
        mag = lambda name:-2.5 * np.log10(s.get(name)) + s.get('zeropoint')
        print s.get('fakeId'), s.get('centroid.sdss')[0], s.get('centroid.sdss')[1], mag('cmodel.flux'), 
        print s.get('deblend.nchild'), mag('flux.kron')

    
if __name__=='__main__':
    main()
