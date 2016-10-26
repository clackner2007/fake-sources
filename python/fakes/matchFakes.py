#!/usr/bin/env python
"""
matchFakes.py.

Matches fakes based on position stored in the calibrated exposure image header
"""

from __future__ import division

import re
import argparse
import collections
import numpy as np
import astropy.table
from distutils.version import StrictVersion

import lsst.daf.persistence as dafPersist
import lsst.afw.geom.ellipses
import lsst.afw.geom
import lsst.pex.exceptions
from lsst.afw.table import SourceCatalog, SchemaMapper

NO_FOOTPRINT = lsst.afw.table.SOURCE_IO_NO_FOOTPRINTS


def combineWithForce(meas, force):
    """Combine the meas and forced_src catalogs."""
    if len(meas) != len(force):
        raise Exception("# Meas and Forced_src catalogs should have " +
                        "the same size!")
    mapper = SchemaMapper(meas.schema)
    mapper.addMinimalSchema(meas.schema)
    newSchema = mapper.getOutputSchema()
    # Add new fields
    newSchema.addField('force.deblend.nchild', type=int)
    newSchema.addField('force.classification.extendedness', type=float)
    newSchema.addField('force.flux.kron', type=float)
    newSchema.addField('force.flux.kron.err', type=float)
    newSchema.addField('force.flux.psf', type=float)
    newSchema.addField('force.flux.psf.err', type=float)
    newSchema.addField('force.flux.kron.apcorr', type=float)
    newSchema.addField('force.flux.kron.apcorr.err', type=float)
    newSchema.addField('force.flux.psf.apcorr', type=float)
    newSchema.addField('force.flux.psf.apcorr.err', type=float)
    newSchema.addField('force.cmodel.flux', type=float)
    newSchema.addField('force.cmodel.flux.err', type=float)
    newSchema.addField('force.cmodel.fracDev', type=float)
    newSchema.addField('force.cmodel.exp.flux', type=float)
    newSchema.addField('force.cmodel.exp.flux.err', type=float)
    newSchema.addField('force.cmodel.dev.flux', type=float)
    newSchema.addField('force.cmodel.dev.flux.err', type=float)
    newSchema.addField('force.cmodel.flux.apcorr', type=float)
    newSchema.addField('force.cmodel.flux.apcorr.err', type=float)
    newSchema.addField('force.cmodel.exp.flux.apcorr', type=float)
    newSchema.addField('force.cmodel.exp.flux.apcorr.err', type=float)
    newSchema.addField('force.cmodel.dev.flux.apcorr', type=float)
    newSchema.addField('force.cmodel.dev.flux.apcorr.err', type=float)

    newCols = ['deblend.nchild', 'classification.extendedness',
               'flux.kron', 'flux.kron.err',
               'flux.psf', 'flux.psf.err',
               'flux.kron.apcorr', 'flux.kron.apcorr.err',
               'flux.psf.apcorr', 'flux.psf.apcorr.err',
               'cmodel.flux', 'cmodel.flux.err',
               'cmodel.flux', 'cmodel.flux.err',
               'cmodel.flux.apcorr', 'cmodel.flux.apcorr.err',
               'cmodel.exp.flux', 'cmodel.exp.flux.err',
               'cmodel.exp.flux.apcorr', 'cmodel.exp.flux.apcorr.err',
               'cmodel.dev.flux', 'cmodel.dev.flux.err',
               'cmodel.dev.flux.apcorr', 'cmodel.dev.flux.apcorr.err',
               'cmodel.fracDev']
    combSrc = SourceCatalog(newSchema)
    combSrc.extend(meas, mapper=mapper)

    for key in newCols:
        combSrc['force.' + key][:] = force[key][:]

    for name in ("Centroid", "Shape"):
        val = getattr(meas.table, "get" + name + "Key")()
        err = getattr(meas.table, "get" + name + "ErrKey")()
        flag = getattr(meas.table, "get" + name + "FlagKey")()
        getattr(combSrc.table, "define" + name)(val, err, flag)

    return combSrc


def getMag(flux, fluxerr, zeropoint):
    """Return the magnitude and error."""
    mag = -2.5 * np.log10(flux)
    magerr = (2.5 / np.log(10.0) * fluxerr / flux)
    return (mag.T + zeropoint).T, magerr


def getEllipse(quad):
    """Return the Re, b/a and PA for a given quadrupole moment."""
    e = lsst.afw.geom.ellipses.Axes(quad)
    rad = e.getA()
    try:
        b_a = (e.getB() / e.getA())
    except ZeroDivisionError:
        b_a = np.nan
    pa = (e.getTheta() * 180.0 / np.pi)
    return rad, b_a, pa


def matchToFakeCatalog(sources, fakeCatalog):
    """
    Match to the fake catalog and append those columns to the source table.

    this assumes the sources are an astropy table
    or it will throw a TypeError
    """
    if not isinstance(sources, astropy.table.Table):
        raise TypeError("Expect an astropy table for sources" +
                        " use getAstroTable to convert")

    fakes = astropy.table.Table().read(fakeCatalog)
    fakes.rename_column('ID', 'fakeId')
    return astropy.table.join(sources, fakes, keys='fakeId', join_type='left')


def getFakeMatchesHeader(cal_md, sources, tol=1.0):
    """
    Return the fake matches based on the information in the header.

    returns a tuple with:
    the positions in pixels of the fake sources added to the chip
    the match is in a dictionary of the form:
        {fakeid:[ind_of_match_in_sources,...],...}

    look within a tolerance of 1 pixel in each direction
    """
    fakeXY = collections.defaultdict(tuple)
    fakename = re.compile('FAKE([0-9]+)')
    for card in cal_md.names():
        m = fakename.match(card)
        if m is not None:
            x, y = map(float, (cal_md.get(card)).split(','))
            fakeXY[int(m.group(1))] = (x, y)

    srcX, srcY = sources.getX(), sources.getY()
    srcIndex = collections.defaultdict(list)
    for fid, fcoord in fakeXY.items():
        distX = srcX - fcoord[0]
        distY = srcY - fcoord[1]
        matched = (np.abs(distX) < tol) & (np.abs(distY) < tol)
        srcIndex[fid] = np.where(matched)[0]

    return fakeXY, srcIndex


def getFakeMatchesRaDec(sources, radecCatFile, bbox, wcs, tol=1.0,
                        reffMatch=False, pix=0.168, minRad=None,
                        raCol='RA', decCol='Dec'):
    """
    Return the fake matches based on an radec match.

    Args:
        sources: source table object
        radecCatFile: filename for fits file of fake object table,
                      including ra/dec
        bbox: Bounding Box of exposure (ccd or patch) within which
              to match fakes
        wcs: Wcs of source image

    KeywordArgs:
        tol: tolerance within which to match sources, given in PIXELS

    Returns:
        fakeXY: set of pixel positions of fake sources
        srcIdx: matches to fake sources in a dictionary of the form
        {fakeid:[ind_of_match_in_sources,...],...}

    Raise:
        IOError: couldn't open radecCatFile
    """
    fakeXY = collections.defaultdict(tuple)
    try:
        fakeCat = astropy.table.Table().read(radecCatFile, format='fits')
    except IOError:
        raise

    for fakeSrc in fakeCat:
        fakeCoord = wcs.skyToPixel(lsst.afw.geom.Angle(fakeSrc[raCol],
                                                       lsst.afw.geom.degrees),
                                   lsst.afw.geom.Angle(fakeSrc[decCol],
                                                       lsst.afw.geom.degrees))
        if bbox.contains(fakeCoord):
            if reffMatch:
                fakeXY[int(fakeSrc['ID'])] = (fakeCoord.getX(),
                                              fakeCoord.getY(),
                                              (fakeSrc['reff'] / pix) * tol)
            else:
                fakeXY[int(fakeSrc['ID'])] = (fakeCoord.getX(),
                                              fakeCoord.getY(),
                                              tol)

    srcX, srcY = sources.getX(), sources.getY()
    srcIndex = collections.defaultdict(list)
    srcClose = collections.defaultdict(list)
    for fid, fcoord in fakeXY.items():
        distX = (srcX - fcoord[0])
        distY = (srcY - fcoord[1])
        distR = np.sqrt((np.abs(distX) ** 2.0) + (np.abs(distY) ** 2.0))
        closest = np.nanargmin(distR)
        radMatch = fcoord[2]
        if minRad is not None:
            if radMatch < minRad:
                radMatch = minRad
        if reffMatch:
            matched = (distR <= radMatch)
        else:
            matched = (np.abs(distX) <= radMatch) & (np.abs(distY) <= radMatch)

        srcIndex[fid] = np.where(matched)[0]
        srcClose[fid] = closest

    return fakeXY, srcIndex, srcClose


def getFakeSources(butler, dataId, tol=1.0,
                   extraCols=('zeropoint', 'visit', 'ccd'),
                   includeMissing=False, footprints=False, radecMatch=None,
                   multiband=False, reffMatch=False, pix=0.168, minRad=None,
                   raCol='RA', decCol='Dec'):
    """
    Get list of sources which agree in pixel position with fake ones with tol.

    This returns a sourceCatalog of all the matched fake objects,
    note, there will be duplicates in this list, since I haven't
    checked deblend.nchild, and I'm only doing a tolerance match,
    which could include extra sources

    The outputs can include extraCols as long as they are one of:
        zeropoint, visit, ccd, thetaNorth, pixelScale

    If includeMissing is true, then the pipeline looks at the fake sources
    added in the header and includes an entry in the table for sources without
    any measurements, specifically the 'id' column will be 0

    radecMatch is the fakes table. if it's not None(default), then do an ra/dec
    match with the input catalog instead of looking in the header for where the
    sources where added
    """
    pipeVersion = dafPersist.eupsVersions.EupsVersions().versions['hscPipe']
    if StrictVersion(pipeVersion) >= StrictVersion('3.9.0'):
        coaddData = "deepCoadd_calexp"
        coaddMeta = "deepCoadd_calexp_md"
    else:
        coaddData = "deepCoadd"
        coaddMeta = "deepCoadd_md"

    availExtras = {'zeropoint': {'type': float, 'doc': 'zeropoint'},
                   'visit': {'type': int, 'doc': 'visit id'},
                   'ccd': {'type': int, 'doc': 'ccd id'},
                   'thetaNorth': {'type': lsst.afw.geom.Angle,
                                  'doc': 'angle to north'},
                   'pixelScale': {'type': float,
                                  'doc': 'pixelscale in arcsec/pixel'}}

    if not np.in1d(extraCols, availExtras.keys()).all():
        print "extraCols must be in ", availExtras

    try:
        if 'filter' not in dataId:
            sources = butler.get('src', dataId,
                                 flags=lsst.afw.table.SOURCE_IO_NO_FOOTPRINTS,
                                 immediate=True)
            cal = butler.get('calexp', dataId, immediate=True)
            cal_md = butler.get('calexp_md', dataId, immediate=True)
        else:
            meas = butler.get('deepCoadd_meas', dataId,
                              flags=NO_FOOTPRINT,
                              immediate=True)
            force = butler.get('deepCoadd_forced_src', dataId,
                               flags=NO_FOOTPRINT,
                               immediate=True)
            sources = combineWithForce(meas, force)
            cal = butler.get(coaddData, dataId, immediate=True)
            cal_md = butler.get(coaddMeta, dataId, immediate=True)
    except (lsst.pex.exceptions.LsstException, RuntimeError):
        print "skipping", dataId
        return None

    if ('pixelScale' in extraCols) or ('thetaNorth' in extraCols):
        wcs = cal.getWcs()
        availExtras['pixelScale']['value'] = wcs.pixelScale().asArcseconds()
        availExtras['thetaNorth']['value'] = lsst.afw.geom.Angle(
            np.arctan2(*tuple(wcs.getLinearTransform().invert()
                              (lsst.afw.geom.Point2D(1.0, 0.0)))))
    if 'visit' in extraCols:
        availExtras['visit']['value'] = dataId['visit']
    if 'ccd' in extraCols:
        availExtras['ccd']['value'] = dataId['ccd']
    if 'zeropoint' in extraCols:
        zeropoint = 2.5 * np.log10(cal_md.get('FLUXMAG0'))
        availExtras['zeropoint']['value'] = zeropoint

    if radecMatch is None:
        fakeXY, srcIndex = getFakeMatchesHeader(cal_md, sources, tol=tol)
    else:
        if minRad is not None:
            print "# The min matching radius is %4.1f pixel" % minRad
        bbox = lsst.afw.geom.Box2D(cal.getBBox(lsst.afw.image.PARENT))
        fakeXY, srcIndex, srcClose = getFakeMatchesRaDec(sources,
                                                         radecMatch,
                                                         bbox,
                                                         cal.getWcs(),
                                                         tol=tol,
                                                         reffMatch=reffMatch,
                                                         pix=pix,
                                                         minRad=minRad,
                                                         raCol=raCol,
                                                         decCol=decCol)

    mapper = SchemaMapper(sources.schema)
    mapper.addMinimalSchema(sources.schema)
    newSchema = mapper.getOutputSchema()
    newSchema.addField('fakeId', type=int,
                       doc='id of fake source matched to position')
    newSchema.addField('nMatched', type=int,
                       doc='Number of matched objects')
    newSchema.addField('nPrimary', type=int,
                       doc='Number of unique matched objects')
    newSchema.addField('nNoChild', type=int,
                       doc='Number of matched objects with nchild==0')
    newSchema.addField('rMatched', type=float,
                       doc='Radius used form atching obects, in pixel')
    newSchema.addField('fakeOffX', type=float,
                       doc='offset from input fake position in X (pixels)')
    newSchema.addField('fakeOffY', type=float,
                       doc='offset from input fake position in Y (pixels)')
    newSchema.addField('fakeOffR', type=float,
                       doc='offset from input fake position in radius')
    newSchema.addField('fakeClosest', type="Flag",
                       doc='Is this match the closest one?')

    for extraName in set(extraCols).intersection(availExtras):
        newSchema.addField(extraName, type=availExtras[extraName]['type'],
                           doc=availExtras[extraName]['doc'])

    srcList = SourceCatalog(newSchema)
    srcList.reserve(sum([len(s) for s in srcIndex.values()]) +
                    (0 if not includeMissing else srcIndex.values().count([])))

    centroidKey = sources.schema.find('centroid.sdss').getKey()
    isPrimary = sources.schema.find('detect.is-primary').getKey()
    nChild = sources.schema.find('force.deblend.nchild').getKey()
    for ident, sindlist in srcIndex.items():
        rMatched = fakeXY[ident][2]
        if minRad is not None:
            if rMatched < minRad:
                rMatched = minRad
        nMatched = len(sindlist)
        nPrimary = np.sum([sources[obj].get(isPrimary) for obj in sindlist])
        nNoChild = np.sum([(sources[obj].get(nChild) == 0) for
                           obj in sindlist])
        if includeMissing and (nMatched == 0):
            newRec = srcList.addNew()
            newRec.set('fakeId', ident)
            newRec.set('id', 0)
            newRec.set('nMatched', 0)
            newRec.set('rMatched', rMatched)
        for ss in sindlist:
            newRec = srcList.addNew()
            newRec.assign(sources[ss], mapper)
            newRec.set('fakeId', ident)
            newRec.set('nMatched', nMatched)
            newRec.set('nPrimary', nPrimary)
            newRec.set('nNoChild', nNoChild)
            newRec.set('rMatched', rMatched)
            offsetX = (sources[ss].get(centroidKey).getX() -
                       fakeXY[ident][0])
            newRec.set('fakeOffX', offsetX)
            offsetY = (sources[ss].get(centroidKey).getY() -
                       fakeXY[ident][1])
            newRec.set('fakeOffY', offsetY)
            newRec.set('fakeOffR', np.sqrt(offsetX ** 2.0 + offsetY ** 2.0))
            if radecMatch:
                if ss == srcClose[ident]:
                    newRec.set('fakeClosest', True)
                else:
                    newRec.set('fakeClosest', False)

    if includeMissing:
        srcList = srcList.copy(deep=True)

    for extraName in set(extraCols).intersection(availExtras):
        tempCol = srcList.get(extraName)
        tempCol.fill(availExtras[extraName]['value'])

    return srcList


def getAstroTable(src, mags=True):
    """
    Return an astropy table with all the src entries.

    if the entries are complex objects, it breaks them down:
      ellipse entries are broken into
           ellipse_a = semi-major axis
           ellipse_q = axis ratio (always < 1)
           ellipse_theta = rotation of semi-major axis
                           from chip x-axis in degrees
    if mags is True, returns the magnitudes for all the flux columns
    """
    tab = astropy.table.Table()
    for name in src.schema.getNames():
        # For reasons I don't understand a lookup by name is much
        #  slower than a lookup by key
        nameKey = src.schema.find(name).getKey()
        try:
            tab.add_column(astropy.table.Column(name=name,
                                                data=src.get(nameKey)))
        except lsst.pex.exceptions.LsstException:
            quadrupole = lsst.afw.geom.ellipses.ellipsesLib.Quadrupole
            icrscoord = lsst.afw.coord.coordLib.IcrsCoord
            if type(src[0].get(nameKey)) is quadrupole:
                """Check for shape measurements"""
                reff, q, theta = zip(*[getEllipse(s.get(nameKey))
                                       for s in src])
                tab.add_column(astropy.table.Column(name=name+'_a',
                               data=reff))
                tab.add_column(astropy.table.Column(name=name+'_q',
                               data=q))
                tab.add_column(astropy.table.Column(name=name+'_theta',
                               data=theta))
            elif type(src[0].get(nameKey)) is icrscoord:
                """Check for coordinate measurements"""
                x, y = zip(*[(s.get(nameKey).getRa().asDegrees(),
                              s.get(nameKey).getDec().asDegrees())
                             for s in src])
                tab.add_column(astropy.table.Column(name=name+'_ra', data=x))
                tab.add_column(astropy.table.Column(name=name+'_dec', data=y))
            else:
                keyData = np.array([s.get(nameKey) for s in src])
                tab.add_column(astropy.table.Column(name=name,
                                                    data=keyData))

        if isinstance(src[0].get(nameKey), lsst.afw.geom.Angle):
            # Report angles in degrees
            tab.remove_column(name)
            newCol = astropy.table.Column(data=[s.get(nameKey).asDegrees()
                                                for s in src],
                                          dtype=float, name=name)
            tab.add_column(newCol)

    if mags:
        # This is a horrible hack, but I don't think we can use the slots,
        # since not all the fluxes end up in the slots
        for col in tab.colnames:
            colMatch = (re.match('^flux\.[a-z]+$', col) or
                        re.match('^flux\.[a-z]+.apcorr$', col) or
                        re.match('^force.flux\.[a-z]+$', col) or
                        re.match('^force.flux\.[a-z]+.apcorr$', col) or
                        re.match('^force.cmodel.+flux$', col) or
                        re.match('^force.cmodel.+flux.apcorr$', col) or
                        re.match('^cmodel.+flux$', col) or
                        re.match('^cmodel.+flux.apcorr$', col))
            if colMatch:
                zp = tab['zeropoint'] if not re.search('apcorr', col) else 0.0
                mag, magerr = getMag(tab[col], tab[col+'.err'], zp)
                tab.add_column(astropy.table.Column(name=re.sub('flux', 'mag',
                                                                col),
                                                    data=mag))
                tab.add_column(astropy.table.Column(name=re.sub('flux', 'mag',
                                                                col+'.err'),
                                                    data=magerr))

    return tab


def returnMatchSingle(butler, slist, visit, ccd,
                      filt=None, tol=1.0, pix=0.168,
                      fakeCat=None, pixMatch=False, multiband=False,
                      reffMatch=False, includeMissing=True, minRad=None,
                      raCol='RA', decCol='Dec'):
        """Return matched catalog for each CCD or Patch."""
        if filt is None:
            print 'Doing ccd %d' % int(ccd)
            mlis = getFakeSources(butler,
                                  {'visit': visit, 'ccd': int(ccd)},
                                  includeMissing=includeMissing,
                                  extraCols=('visit', 'ccd',
                                             'zeropoint', 'pixelScale',
                                             'thetaNorth'),
                                  radecMatch=fakeCat if not pixMatch else None,
                                  tol=tol, reffMatch=reffMatch, pix=pix,
                                  minRad=minRad, raCol=raCol, decCol=decCol)
        else:
            print 'Doing patch %s' % ccd
            mlis = getFakeSources(butler,
                                  {'tract': visit, 'patch': ccd,
                                   'filter': filt},
                                  includeMissing=includeMissing,
                                  extraCols=('thetaNorth', 'pixelScale',
                                             'zeropoint'),
                                  radecMatch=fakeCat if not pixMatch else None,
                                  tol=tol, multiband=multiband,
                                  reffMatch=reffMatch, pix=pix,
                                  minRad=minRad, raCol=raCol, decCol=decCol)

        if mlis is None:
            print '   No match returns!'
        else:
            if slist is None:
                slist = mlis.copy(True)
            else:
                slist.extend(mlis, True)
            del mlis

        return slist


def returnMatchTable(rootDir, visit, ccdList, outfile=None, fakeCat=None,
                     overwrite=False, filt=None, tol=1.0, pixMatch=False,
                     multiband=False, reffMatch=False, pix=0.168,
                     multijobs=1, includeMissing=True, minRad=None,
                     raCol='RA', decCol='Dec'):
    """
    Driver (main function) for return match to fakes.

    INPUT: rootDir = rerun directory
           visit = visit id (int) (or tracts)
           ccdList = list of ccds to look at (or patches)
           outdir = output directory for matched file,
                    None means no output written
           fakeCat = fake catalog to match to,
                     None means the fake sources are just
                     extracted from the header of the CCDs based on
                     position but no matching is done
           overwrite = whether to overwrite the existing output file,
                       default is False
           pixMatch = do pixel matching instead of ra/dec matching
                      even if there is a catalog supplied
           multiband = whether match to forced photometry catalogs
                       from multiband process
           reffMatch = whether match fake sources in pixel radius
                       or using tol x Reff (Only for Ra, Dec match)
    OUTPUT: returns an astropy.table.Table with all the entries
            from the source catalog for objects which match in pixel
            position to the fake sources
    """
    butler = dafPersist.Butler(rootDir)
    slist = None

    if multijobs > 1:
        try:
            from joblib import Parallel, delayed
            mlist = Parallel(n_jobs=multijobs)(delayed(returnMatchSingle)(
                                               butler, None, visit, ccd,
                                               filt=filt,
                                               fakeCat=fakeCat,
                                               includeMissing=includeMissing,
                                               pixMatch=pixMatch,
                                               reffMatch=reffMatch, tol=tol,
                                               multiband=multiband,
                                               minRad=minRad,
                                               pix=pix,
                                               decCol=decCol,
                                               raCol=raCol) for ccd in ccdList)
            for m in mlist:
                if m is not None:
                    if slist is None:
                        slist = m.copy(True)
                    else:
                        slist.extend(m, True)
                    del m
        except ImportError:
            print "# Can not import joblib, stop multiprocessing!"
            for ccd in ccdList:
                slist = returnMatchSingle(butler, slist, visit, ccd,
                                          filt=filt, fakeCat=fakeCat,
                                          includeMissing=includeMissing,
                                          pixMatch=pixMatch,
                                          reffMatch=reffMatch,
                                          tol=tol, pix=pix,
                                          multiband=multiband,
                                          minRad=minRad,
                                          raCol=raCol, decCol=decCol)
    else:
        for ccd in ccdList:
            slist = returnMatchSingle(butler, slist, visit, ccd,
                                      filt=filt, fakeCat=fakeCat,
                                      includeMissing=includeMissing,
                                      pixMatch=pixMatch,
                                      reffMatch=reffMatch,
                                      tol=tol, pix=pix,
                                      multiband=multiband,
                                      minRad=minRad,
                                      raCol=raCol, decCol=decCol)

    if slist is None:
        print "Returns no match....!"

        return None
    else:
        astroTable = getAstroTable(slist, mags=True)

        if fakeCat is not None:
            astroTable = matchToFakeCatalog(astroTable, fakeCat)

        if outfile is not None:
            try:
                astroTable.write(outfile+'.fits', format='fits',
                                 overwrite=overwrite)
            except IOError:
                print "Try setting the option -w to overwrite the file."
                raise

        return astroTable


if __name__ == '__main__':
    # TODO: this should use the LSST/HSC conventions
    parser = argparse.ArgumentParser()
    parser.add_argument('rootDir', help='root dir of data repo')
    parser.add_argument('visit',
                        help='id of visit (or tract, if filter is specified)',
                        type=int)
    parser.add_argument('-f', '--filter', dest='filt',
                        help='name of filter, if none assume single visit',
                        default=None)
    parser.add_argument('--ccd', nargs='+', help='id of ccd(s) or patches')
    parser.add_argument('-o', help='outputfilename', default=None,
                        dest='outfile')
    parser.add_argument('-c', help='fake catalog', default=None,
                        dest='fakeCat')
    parser.add_argument('-w', '--overwrite', help='overwrite output file',
                        dest='ow', default=False, action='store_true')
    parser.add_argument('-m', '--multiband',
                        help='Match multiband measurements',
                        dest='multiband', default=False, action='store_true')
    parser.add_argument('-r', '--reffMatch',
                        help='Match the fake sources using tol x Reff',
                        dest='reffMatch', default=False, action='store_true')
    parser.add_argument('--min', '--minRad',
                        help='Minimum matching radius in unit of pixel',
                        dest='minRad', type=float, default=None)
    parser.add_argument('-t', '--tolerance', type=float, dest='tol',
                        help='matching radius in PIXELS (default=1.0)')
    parser.add_argument('-j', '--multijobs', type=int,
                        help='Number of jobs run at the same time',
                        dest='multijobs', default=1)
    parser.add_argument('--ra', '--raCol', dest='raCol',
                        help='Name of the column for RA',
                        default='RA')
    parser.add_argument('--dec', '--decCol', dest='decCol',
                        help='Name of the column for Dec',
                        default='Dec')
    args = parser.parse_args()

    returnMatchTable(args.rootDir, args.visit, args.ccd, args.outfile,
                     args.fakeCat, overwrite=args.ow, filt=args.filt,
                     tol=args.tol, multiband=args.multiband,
                     reffMatch=args.reffMatch,
                     multijobs=args.multijobs,
                     minRad=args.minRad,
                     raCol=args.raCol, decCol=args.decCol)
