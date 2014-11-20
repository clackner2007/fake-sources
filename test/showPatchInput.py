#!/usr/bin/env python

import argparse
import lsst.daf.persistence as dafPersist
import lsst.afw.image as afwImage

def main(butler, dataId, coaddType='deepCoadd'):

    coadd = butler.get(coaddType, **dataId)
    visitInputs = coadd.getInfo().getCoaddInputs().visits

    ccdInputs = coadd.getInfo().getCoaddInputs().ccds

    for v, ccd in zip(ccdInputs.get("visit"), ccdInputs.get("ccd")):
        print "%d  %d" % (v, ccd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("root",  help="Root directory of data repository")
    parser.add_argument("tract", type=int, help="Patch to use")
    parser.add_argument("patch", type=str, help="Patch to use")
    parser.add_argument("filter", type=str, help="Filter to use")
    args = parser.parse_args()

    butler = dafPersist.Butler(args.root)
    dataId = {'tract':args.tract, 'patch':args.patch, 'filter':args.filter}

    main(butler, dataId)

