import numpy as np

import lsst.afw.image
import lsst.afw.geom
import lsst.afw.math
import lsst.afw.cameraGeom
import lsst.afw.coord
import lsst.pex.config
from lsst.pipe.tasks.fakes import FakeSourcesConfig, FakeSourcesTask
import pyfits as fits

import FakeSourceLib as fsl

class PositionStarFakesConfig(FakeSourcesConfig):
    starList = lsst.pex.config.Field(dtype=str, doc="catalog of stars with mags ra/dec to add")
    seed = lsst.pex.config.Field(dtype=int, default=1,
                                 doc="Seed for random number generator")

class PositionStarFakesTask(FakeSourcesTask):
    ConfigClass = PositionStarFakesConfig

    def __init__(self, **kwargs):
        FakeSourcesTask.__init__(self, **kwargs)
        print "RNG seed:", self.config.seed
        self.rng = lsst.afw.math.Random(self.config.seed)
        self.npRand = np.random.RandomState(self.config.seed)
        self.starData = fits.open(self.config.starList)[1].data


    def run(self, exposure, background):

        self.log.info("Adding fake stars at real positions")
        psf = exposure.getPsf()
        psfBBox = psf.computeImage().getBBox()
        margin =  max(psfBBox.getWidth(), psfBBox.getHeight())/2 + 1

        md = exposure.getMetadata()
        expBBox = exposure.getBBox(lsst.afw.image.PARENT)
        wcs = exposure.getWcs()
        skyToPixelMatrix=wcs.getLinearTransform().invert().getMatrix()/3600.0

        for istar, star in enumerate(self.starData):
            try:
                starident = star["ID"]
            except KeyError:
                starident = istar + 1

            try:
                flux = exposure.getCalib().getFlux(float(star['mag']))
            except KeyError:
                raise KeyError("No mag column in %s table"%self.config.starList)

            try:
                starCoord = lsst.afw.coord.Coord(lsst.afw.geom.Point2D(star['RA'], star['DEC']))
            except KeyError:
                raise("No RA/DEC column in %s table"%self.config.starList)

            starXY = wcs.skyToPixel(starCoord)
            bboxI = exposure.getBBox(lsst.afw.image.PARENT)
            bboxI.grow(margin)
            if not bboxI.contains(lsst.afw.geom.Point2I(starXY)):
                #self.log.info("Skipping fake %d"%starident)
                continue

            starImage = psf.computeImage(starXY)
            starImage *= flux
            starBBox = starImage.getBBox(lsst.afw.image.PARENT)

           #check that we're within the larger exposure, otherwise crop
            if expBBox.contains(starBBox) is False:
                newBBox = starImage.getBBox(lsst.afw.image.PARENT)
                newBBox.clip(expBBox)
                if newBBox.getArea() <= 0:
                    self.log.info("Skipping fake %d"%starident)
                    continue
                self.log.info("Cropping FAKE%d from %s to %s"%(starident, str(starBBox), str(newBBox)))
                starImage = starImage.Factory(starImage, newBBox, lsst.afw.image.PARENT)
                starBBox = newBBox

            starMaskedImage = fsl.addNoise(starImage.convertF(), exposure.getDetector(),
                                           rand_gen=self.npRand)

            starMaskedImage.getMask().set(self.bitmask)

            md.set("FAKE%s" % str(starident), "%.3f, %.3f" % (starXY.getX(), starXY.getY()))
            self.log.info("Adding fake %s at: %.1f,%.1f"% (str(starident), starXY.getX(), starXY.getY()))

            subMaskedImage = exposure.getMaskedImage().Factory(exposure.getMaskedImage(),
                                                               starMaskedImage.getBBox(lsst.afw.image.PARENT),
                                                               lsst.afw.image.PARENT)
            subMaskedImage += starMaskedImage
