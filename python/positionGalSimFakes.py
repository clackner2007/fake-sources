import numpy as np

import lsst.afw.image
import lsst.afw.geom
import lsst.afw.math
import lsst.afw.cameraGeom
import lsst.afw.coord
import lsst.pex.config
from lsst.pipe.tasks.fakes import FakeSourcesConfig, FakeSourcesTask
import pyfits as fits

import makeFakeGalaxy as makeFake
import FakeSourceLib as fsl

class PositionGalSimFakesConfig(FakeSourcesConfig):
    galList = lsst.pex.config.Field(dtype=str, doc="catalog of galaxies to add")
    maxMargin = lsst.pex.config.Field(dtype=int, default=600, optional=True,
                                   doc="Size of margin = 1/2 of maximum galsim image size, in pixels")
    seed = lsst.pex.config.Field(dtype=int, default=1,
                                 doc="Seed for random number generator")
    galType = lsst.pex.config.ChoiceField(dtype=str, default='sersic',
                                          allowed={'dsersic':'double sersic galaxies added',
                                                   'sersic':'single sersic galaxies added',
                                                   'real':'real HST galaxy images added'},
                                          doc='type of GalSim galaxies to add')
    

class PositionGalSimFakesTask(FakeSourcesTask):
    ConfigClass = PositionGalSimFakesConfig

    def __init__(self, **kwargs):
        FakeSourcesTask.__init__(self, **kwargs)
        print "RNG seed:", self.config.seed
        self.rng = lsst.afw.math.Random(self.config.seed)
        self.npRand = np.random.RandomState(self.config.seed)
        self.galData = fits.open(self.config.galList)[1].data


    def run(self, exposure, background):

        self.log.info("Adding fake galaxies at real positions")
        psf = exposure.getPsf()
        md = exposure.getMetadata()
        expBBox = exposure.getBBox(lsst.afw.image.PARENT)
        wcs = exposure.getWcs()

        for igal, gal in enumerate(self.galData):
            try:
                galident = gal["ID"]
            except KeyError:
                galident = igal + 1

            try:
                flux = exposure.getCalib().getFlux(float(gal['mag']))
            except KeyError:
                raise KeyError("No mag column in %s table"%self.config.galList)

            try:
                galCoord = lsst.afw.coord.Coord(lsst.afw.geom.Point2D(gal['RA'], gal['DEC']))
            except KeyError:
                raise("No RA/DEC column in %s table"%self.config.galList)

            galXY = wcs.skyToPixel(galCoord)
            bboxI = exposure.getBBox(lsst.afw.image.PARENT)
            bboxI.grow(self.config.maxMargin)
            if not bboxI.contains(lsst.afw.geom.Point2I(galXY)):
                self.log.info("Skipping fake %d"%galident)
                continue
            
            #this is extrapolating for the PSF, probably not a good idea
            psfImage = psf.computeKernelImage(galXY)
            galArray = makeFake.makeGalaxy( flux, gal, psfImage.getArray(), self.config.galType )
            galImage = lsst.afw.image.ImageF(galArray.astype(np.float32))
            galBBox = galImage.getBBox(lsst.afw.image.PARENT)
            galImage = lsst.afw.math.offsetImage(galImage,
                                                 galXY.getX() - galBBox.getWidth()/2.0 + 0.5,
                                                 galXY.getY() - galBBox.getHeight()/2.0 + 0.5,
                                                 'lanczos3')
            galBBox = galImage.getBBox(lsst.afw.image.PARENT)

            
           #check that we're within the larger exposure, otherwise crop
            if expBBox.contains(galImage.getBBox(lsst.afw.image.PARENT)) is False:
                newBBox = galImage.getBBox(lsst.afw.image.PARENT)
                newBBox.clip(expBBox)
                if newBBox.getArea() <= 0:
                    self.log.info("Skipping fake %d"%galident)
                    continue
                self.log.info("Cropping FAKE%d from %s to %s"%(galident, str(galBBox), str(newBBox)))
                galImage = galImage.Factory(galImage, newBBox, lsst.afw.image.PARENT)
                galBBox = newBBox

            galMaskedImage = fsl.addNoise(galImage, exposure.getDetector(), rand_gen=self.npRand)
            
            md.set("FAKE%s" % str(galident), "%.3f, %.3f" % (galXY.getX(), galXY.getY()))
            self.log.info("Adding fake %s at: %.1f,%.1f"% (str(galident), galXY.getX(), galXY.getY()))

            galMaskedImage.getMask().set(self.bitmask)
            subMaskedImage = exposure.getMaskedImage().Factory(exposure.getMaskedImage(),
                                                               galMaskedImage.getBBox(lsst.afw.image.PARENT),
                                                               lsst.afw.image.PARENT)
            subMaskedImage += galMaskedImage

