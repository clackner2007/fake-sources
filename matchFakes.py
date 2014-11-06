#!/usr/bin/env python
"""
matchFakes.py
matches fakes based on position stored in the calibrated exposure image header
"""

import lsst.daf.persistence as dafPersist
from lsst.afw.table import SourceCatalog, SchemaMapper
import numpy as np
import argparse
import re
import collections

def getFakeSources(rootdir, dataId, tol=1.0):
    """Get list of sources which agree in position with fake ones with tol
    """
    butler = dafPersist.Butler(rootdir)
    
    sources = butler.get('src', dataId)
    cal_md = butler.get('calexp_md', dataId)


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
    srcList = SourceCatalog(newSchema)
    srcList.reserve(sum([len(s) for s in srcIndex.values()]))

    for ident, sindlist in srcIndex.items():
        for ss in sindlist:
            newRec = srcList.addNew()
            newRec.assign(sources[ss], mapper)
            newRec.set('fakeId', ident)
    return srcIndex, srcList


def main():

    #TODO: this should use the LSST/HSC conventions
    parser = argparse.ArgumentParser()
    parser.add_argument('rootDir', help='root dir of data repo')
    parser.add_argument('visit', help='id of visit', type=int)
    parser.add_argument('ccd', help='id of ccd', type=int)
    args = parser.parse_args()
    
    sind, slist = getFakeSources(args.rootDir, 
                                 {'visit':args.visit, 'ccd':args.ccd})

    butler = dafPersist.Butler(args.rootDir)
    md = butler.get('calexp_md', {'visit':args.visit,
                                  'ccd':args.ccd})
    zp = 2.5 * np.log10(md.get('FLUXMAG0'))
    print 'fakeId X Y cmodel_mag nChild kron_mag'
    for s in slist:
        mag = lambda name:-2.5 * np.log10(s.get(name)) + zp
        print s.get('fakeId'), s.get('centroid.sdss')[0], s.get('centroid.sdss')[1], mag('cmodel.flux'), 
        print s.get('deblend.nchild'), mag('flux.kron')

    
if __name__=='__main__':
    main()
