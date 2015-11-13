#!/usr/bin/env python

import re
import os
import argparse

import collections
import numpy as np
import pyfits as fits
import matplotlib.pyplot as pyplot

import lsst.daf.persistence as dafPersist
import lsst.afw.geom.ellipses as geomEllip
from lsst.afw.table import SourceCatalog, SchemaMapper


def getExpArray(root, tract, patch, filter):

    # make a butler and specify your dataId
    butler = dafPersist.Butler(root)
    dataId = {'tract': tract, 'patch':patch, 'filter':filter}
    dataType = "deepCoadd"

    # get the exposure from the butler
    # Ugly work around in case the before and after Reruns are from different hscPipe
    try:
        exposure = butler.get(dataType, dataId)
    except Exception:
        try:
            exposure = butler.get('deepCoadd', dataId)
        except:
            raise

    # get the maskedImage from the exposure, and the image from the mimg
    mimg = exposure.getMaskedImage()
    img = mimg.getImage()

    # convert to a numpy ndarray
    return img.getArray()


def main(root1, root2, tract, patch, filter, root=""):

    # get the name of the rerun
    rerun = os.path.split(root2)[-1]

    # get the image array before the fake objects are added
    imgBefore = getExpArray(root + root1, tract, patch, filter)
    imgAfter  = getExpArray(root + root2, tract, patch, filter)

    # get the difference between the two image
    imgDiff = (imgAfter - imgBefore)

    # stretch it with arcsinh and make a png with pyplot
    fig, axes = pyplot.subplots(1, 3, sharex=True, sharey=True, figsize=(16.5,5))
    pyplot.subplots_adjust(left=0.04, bottom=0.03, right=0.99, top=0.97,
                           wspace=0.01, hspace = 0.01)

    imgs   = imgBefore, imgAfter, imgDiff
    titles = "Before", "After", "Diff"
    for i in range(3):
        print '### Plot : ', i
        axes[i].imshow(np.arcsinh(imgs[i]), cmap='gray')
        axes[i].set_title(titles[i])

    pyplot.gcf().savefig("%s-%s-%s-%s.png"%(rerun, str(tract), str(patch), str(filter)))


if __name__ == '__main__':

    root = '/lustre/Subaru/SSP/rerun/'

    parser = argparse.ArgumentParser()
    parser.add_argument("root1", help="Root directory of data before adding fake objects")
    parser.add_argument("root2", help="Root directory of data after adding fake objects")
    parser.add_argument("tract", type=int, help="Tract to show")
    parser.add_argument("patch", help="Patch to show")
    parser.add_argument("filter", help="Filter to show")
    args = parser.parse_args()

    main(args.root1, args.root2, args.tract, args.patch, args.filter, root=root)
