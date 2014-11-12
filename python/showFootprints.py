#!/usr/bin/env python
"""
function to show a list of src footprints in a mosaic
"""

import lsst.afw.display.ds9 as ds9
import lsst.afw.display.utils 
import lsst.daf.persistence
import lsst.afw.image
import matchFakes
import numpy.random


def getMosaic(sources, exposure, idname):
    """
    make a ds9 mosaic for the given source list from the given exposure
    
    stolen from psfMosaic.py on the sphinx documentation
    """
    img = exposure.getMaskedImage().getImage()
    subImages=[]
    labels = []
    for src in sources:
        subimg = lsst.afw.image.ImageF(img, src.getFootprint().getBBox(), 
                                       lsst.afw.image.PARENT, True)
        subImages.append(subimg)
        labels.append('ID=%s'%str(src.get(idname)))

    m = lsst.afw.display.utils.Mosaic()
    m.setGutter(2)
    m.setBackground(0)
    m.setMode("square")
    # create the mosaic
    for img in subImages:
        m.append(img)
    mosaic = m.makeMosaic()
    # display it with labels in ds9
    ds9.mtv(mosaic)                
    m.drawLabels(labels)
    


def main(root, visit, ccd, fakes=False, noblends=True, listobj=16):

    butler = lsst.daf.persistence.Butler(root)
    dataId = {'visit':visit, 'ccd':ccd}
    if fakes:
        src = matchFakes.getFakeSources(butler, dataId,
                                        zeropoint=True)
    else:
        src = butler.get('src', dataId)
    if noblends:
        src = [s for s in src if (s.get('deblend.nchild')==0)&(s.get('parent')==0)]


    exposure = butler.get('calexp', dataId)
    
    if type(listobj) is int:
        listobj = numpy.random.choice(range(len(src)), listobj, False)
    
    srcList = [src[i] for i in listobj]
    getMosaic(srcList, exposure, 'fakeId' if fakes else 'id')

    


if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('root', help="Root directory of data repository")
    parser.add_argument("visit", type=int, help="Visit")
    parser.add_argument("ccd", type=int, help="CCD")
    parser.add_argument('-f', '--fake', default=False, action='store_true',
                        help='show fake sources', dest='fake')
    parser.add_argument('-n', '--number', dest='num', help='number of objects to show',
                        default=16, type=int)
    #parser.add_argument('-o', '--outputpath', dest='outpath',
    #                    help='path for output')
    args = parser.parse_args()
    main(args.root, args.visit, args.ccd, fakes=args.fake, listobj=args.num)
