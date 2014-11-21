#!/usr/bin/env python

import argparse
import lsst.daf.persistence as dafPersist

def main(butler, dataId, coaddType='deepCoadd'):

    coadd = butler.get(coaddType, **dataId)
    ccdInputs = coadd.getInfo().getCoaddInputs().ccds

    for i in ccdInputs:
        print "%d  %d" % (i.get("visit"), i.get("ccd"))


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

