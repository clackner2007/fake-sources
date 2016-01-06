#!/usr/bin/env python
# encoding: utf-8
"""Make a catalog of fakes that are highly blended."""

from __future__ import (division, print_function)

import os
import random
import argparse

import numpy as np
from astropy.table import Table, Column


def disturbRaDec(val, mu=1.0, sigma=1.0):
    """Disturb the coordinate a little bit."""
    num = len(val)

    return (np.random.normal(mu, sigma, num) / 3600.0)


def makeBlendedCat(fakeCat, realCat, raCol='ra', decCol='dec',
                   sigma=1.0, mu=1.0):
    """Make a highly blended version of fake catalog."""
    # Fake catalog
    if not os.path.isfile(fakeCat):
        raise Exception('# Can not find input fake catalog : %s' % fakeCat)
    else:
        fakeTab = Table.read(fakeCat, format='fits')
        nFake = len(fakeTab)
        print("# There are %d fake galaxies in the catalog" % nFake)
    # Name of the output catalog
    blendTab = fakeCat.replace('.fits', '_highb.fits')

    # Real catalog
    if not os.path.isfile(realCat):
        raise Exception('# Can not find input real catalog : %s' % realCat)
    else:
        realTab = Table.read(realCat, format='fits')
        nReal = len(realTab)
        print("# There are %d real galaxies in the catalog" % nReal)

    # Randomly select nFake galaxies from the realCat
    indices = random.sample(range(nReal), nFake)

    # Replace the RA, DEC with a small shift
    fakeTab.add_column(Column(realTab[indices][raCol]), name='RA_ori')
    fakeTab.add_column(Column(realTab[indices][decCol]), name='Dec_ori')

    fakeTab['RA'] = (realTab[indices][raCol] + disturbRaDec(realTab[raCol],
                                                            mu=mu,
                                                            sigma=sigma))
    fakeTab['Dec'] = (realTab[indices][decCol] + disturbRaDec(realTab[raCol],
                                                              mu=mu,
                                                              sigma=sigma))

    # Save the new catalog
    fakeTab.write(blendTab, format='fits', overwrite=True)

    return fakeTab


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("fakeCat", help="Input catalog of fake objects")
    parser.add_argument("realCat", help="Catalog of real objects")
    parser.add_argument('--ra', '--raCol', dest='raCol',
                        help='Column for RA in realCat',
                        default='ra')
    parser.add_argument('--dec', '--decCol', dest='decCol',
                        help='Column for DEC in realCat',
                        default='dec')

    args = parser.parse_args()

    makeBlendedCat(args.fakeCat, args.realCat,
                   raCol=args.raCol, decCol=args.decCol,
                   sigma=1.0)
