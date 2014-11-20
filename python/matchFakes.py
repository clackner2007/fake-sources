#!/usr/bin/env python
"""
matchFakes.py
matches fakes based on position stored in the calibrated exposure image header
"""

import lsst.daf.persistence as dafPersist
from lsst.afw.table import SourceCatalog, SchemaMapper
import lsst.afw.geom
import lsst.pex.exceptions
import numpy as np
import argparse
import re
import collections
import astropy.table
import lsst.afw.geom.ellipses

def getMag(flux, fluxerr, zeropoint):
    """
    return the magnitude and error
    """
    mag, magerr = -2.5 * np.log10(flux), 2.5/np.log(10.0)*fluxerr/flux
    return (mag.T + zeropoint).T, magerr


def getEllipse(quad):
    """
    returns the semi-major axis, axes ratio and PA for a given quadrupole moment
    """
    e = lsst.afw.geom.ellipses.Axes(quad)
    return e.getA(), e.getB()/e.getA(), e.getTheta() * 180.0/np.pi


def matchToFakeCatalog(sources, fakeCatalog):
    """
    match to the fake catalog and append those columns to the source table
    
    this assumes the sources are an astropy table
    or it will throw a TypeError
    """
    if not isinstance(sources, astropy.table.Table):
        raise TypeError("expects and astropy table for sources, use getAstroTable to convert")
    
    
    fakes = astropy.table.Table().read(fakeCatalog)
    fakes.rename_column('ID', 'fakeId')
    return astropy.table.join(sources, fakes, keys='fakeId', join_type='left')



def getFakeSources(butler, dataId, tol=1.0, extraCols=('zeropoint', 'visit', 'ccd'),
                   includeMissing=False):
    """Get list of sources which agree in pixel position with fake ones with tol
    
    this returns a sourceCatalog of all the matched fake objects,
    note, there will be duplicates in this list, since I haven't checked deblend.nchild,
    and I'm only doing a tolerance match, which could include extra sources
    
    the outputs can include extraCols as long as they are one of:
      zeropoint, visit, ccd, thetaNorth, pixelScale

    if includeMissing is true, then the pipeline looks at the fake sources
    added in the header and includes an entry in the table for sources without
    any measurements, specifically the 'id' column will be 0
    """
    
    availExtras = {'zeropoint':{'type':float, 'doc':'zeropoint'}, 
                   'visit':{'type':int, 'doc':'visit id'}, 
                   'ccd':{'type':int, 'doc':'ccd id'},
                   'thetaNorth':{'type':lsst.afw.geom.Angle, 'doc':'angle to north'},
                   'pixelScale':{'type':float, 'doc':'pixelscale in arcsec/pixel'}}
    
    if not np.in1d(extraCols, availExtras.keys()).all():
        print "extraCols must be in ",availExtras

    sources = butler.get('src', dataId)
    cal_md = butler.get('calexp_md', dataId)

    if 'pixelScale' or 'thetaNorth' in extraCols:
        wcs = butler.get('calexp', dataId).getWcs()
        availExtras['pixelScale']['value'] =  wcs.pixelScale().asArcseconds()
        availExtras['thetaNorth']['value'] = lsst.afw.geom.Angle(
            np.arctan2(*tuple(wcs.getLinearTransform().invert()
                              (lsst.afw.geom.Point2D(1.0,0.0)))))
    if 'visit' in extraCols:
        availExtras['visit']['value'] = dataId['visit']
    if 'ccd' in extraCols:
        availExtras['ccd']['value'] = dataId['ccd']
    if 'zeropoint' in extraCols:
        availExtras['zeropoint']['value'] = 2.5*np.log10(cal_md.get('FLUXMAG0'))


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
    newSchema.addField('fakeOffset', type=lsst.afw.geom.Point2D,
                       doc='offset from input fake position (pixels)')
    for extraName in set(extraCols).intersection(availExtras):
        newSchema.addField(extraName, type=availExtras[extraName]['type'],
                           doc=availExtras[extraName]['doc'])

    srcList = SourceCatalog(newSchema)
    srcList.reserve(sum([len(s) for s in srcIndex.values()]) + 
                    (0 if not includeMissing else srcIndex.values().count([])))

    for ident, sindlist in srcIndex.items():
        if includeMissing and len(sindlist)==0:
            newRec = srcList.addNew()
            newRec.set('fakeId', ident)
            newRec.set('id', 0)
        for ss in sindlist:
            newRec = srcList.addNew()
            newRec.assign(sources[ss], mapper)
            newRec.set('fakeId', ident)
            newRec.set('fakeOffset', 
                       lsst.afw.geom.Point2D(sources[ss].get('centroid.sdss').getX() - fakeXY[ident][0],
                                             sources[ss].get('centroid.sdss').getY() - fakeXY[ident][1]))

    if includeMissing:
        srcList = srcList.copy(deep=True)

    for extraName in set(extraCols).intersection(availExtras):
        tempCol = srcList.get(extraName)
        tempCol.fill(availExtras[extraName]['value'])

    return srcList


def getAstroTable(srcIn, mags=True):
    """
    returns an astropy table with all the src entries
    if the entries are complex objects, it breaks them down:
      ellipse entries are broken into 
           ellipse_a = semi-major axis
           ellipse_q = axis ratio (always < 1)
           ellipse_theta = rotation of semi-major axis from chip x-axis in degrees 
    if mags is True, returns the magnitudes for all the flux columns
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
        #report angles in degrees
        if isinstance(src[0].get(name), lsst.afw.geom.Angle):
            tab[name] *= 180.0/np.pi


    if mags:
        #this is a horrible hack, but I don't think we can use the slots, since 
        #not all the fluxes end up in the slots
        for col in tab.colnames:
            if (re.match('^flux\.[a-z]+$', col) or 
                re.match('^flux\.[a-z]+.apcorr$', col) or
                re.match('^cmodel.+flux$', col) or 
                re.match('^cmodel.+flux.apcorr$', col)):
                mag, magerr = getMag(tab[col], tab[col+'.err'], tab['zeropoint'])
            
                tab.add_column(astropy.table.Column(name=re.sub('flux', 'mag', col),
                                                    data=mag))
                tab.add_column(astropy.table.Column(name=re.sub('flux', 'mag', col+'.err'),
                                                    data=magerr))
                
    return tab



def returnMatchTable(rootDir, visit, ccdList, outdir=None, fakeCat=None):
    """
    driver (main function) for return match to fakes
    INPUT: rootDir = rerun directory
           visit = visit id (int)
           ccdList = list of ccds to look at 
           outdir = output directory for matched file, None means no output written
           fakeCat = fake catalog to match to, None means the fake sources are just
                     extracted from the header of the CCDs based on position but no matching is done
    OUTPUT: returns an astropy.table.Table with all the entries from the source catalog for 
            objects which match in pixel position to the fake sources
    """
    
    butler = dafPersist.Butler(rootDir)
    slist = None

    for ccd in ccdList:
        temp = getFakeSources(butler,
                              {'visit':visit, 'ccd':ccd}, includeMissing=True,
                              extraCols=('visit', 'ccd', 'zeropoint', 'pixelScale', 'thetaNorth'))
        if slist is None:
            slist = temp.copy(True)
        else:
            slist.extend(temp, True)
        del temp

    table = getAstroTable(slist, mags=True)
    
    if fakeCat is not None:
        table = matchToFakeCatalog(table, args.fakeCat)

    if outdir is not None:        
        table.write(args.outdir+args.rootDir.strip('/').split('/')[-1]+'_matchFakes.fits', format='fits')

    return table

    
if __name__=='__main__':
        #TODO: this should use the LSST/HSC conventions
    parser = argparse.ArgumentParser()
    parser.add_argument('rootDir', help='root dir of data repo')
    parser.add_argument('visit', help='id of visit', type=int)
    parser.add_argument('--ccd', nargs='+', help='id of ccd(s)', type=int)
    parser.add_argument('-o', help='output/dir', default=None, dest='outdir')
    parser.add_argument('-f', help='fake catalog', default=None, dest='fakeCat')
    args = parser.parse_args()

    returnMatchTable(args.rootDir, args.visit, args.ccd, args.outdir, args.fakeCat)
