import numpy as np

import lsst.afw.image
import lsst.afw.geom
import lsst.afw.math
import lsst.pex.config
from lsst.pipe.tasks.fakes import FakeSourcesConfig, FakeSourcesTask


class RandomGalSimFakesConfig(FakeSourcesConfig):
    galList = lsst.pex.config.Field(doc="catalog of galaxies to add")
    margin = lsst.pex.config.Field(dtype=int, default=None, optional=True,
                                   doc="Size of margin at edge that should not be added")
    seed = lsst.pex.config.Field(dtype=int, default=1,
                                 doc="Seed for random number generator")

class RandomGalSimFakesTask(FakeSourcesTask):
    ConfigClass = RandomGalSimFakesConfig

    def __init__(self, **kwargs):
        FakeSourcesTask.__init__(self, **kwargs)
        print "RNG seed:", self.config.seed
        self.rng = lsst.afw.math.Random(self.config.seed)
        self.galData = np.loadtxt(self.config.galList, dtype={'ID':int, 
                                                              'mag':float,
                                                              'sersic_n':float, 
                                                              'reff_pix':float})

    def run(self, exposure, sources, background):

        self.log.info("Adding fake random galaxies")
        psf = exposure.getPsf()

        for igal, gal in enumerate(self.galData):
            flux = exposure.getCalib().getFlux(gal['mag'])
           
            psfImage = psf.computeKernelImage(lsst.afw.geom.Point2D(x, y))

            #TODO: write function that's attached to galsim elsewhere
            galArray = FUNCTION_TO_WRITE(flux, gal['reff_pix'], gal['sersic_n'], psfImage)
            
            #TODO: add variance, get it from amp
            #TODO: shift the image to x,y
            #TODO: check that the margins are sufficient, or crop the object
            #TODO: set the mask
            md = exposure.getMetadata()

            x = self.rng.flat(bboxD.getMinX(), bboxD.getMaxX())
            y = self.rng.flat(bboxD.getMinY(), bboxD.getMaxY())
            
            md.set("FAKE%d" % i, "%.3f, %.3f" % (x, y))
            self.log.info("Adding fake at: %.1f,%.1f"% (x, y))

            galMaskedImage = lsst.afw.image.MaskedImageF(galArray)
            galMaskedImage.getMask().set(self.bitmask)
            subMaskedImage = exposure.getMaskedImage().Factory(exposure.getMaskedImage(),
                                                               galMaskedImage.getBBox(lsst.afw.image.PARENT),
                                                               lsst.afw.image.PARENT)
            subMaskedImage += galMaskedImage

        #deals with margins, needs rewrite
        # psfBBox = psf.computeImage().getBBox()
        # margin = max(psfBBox.getWidth(), psfBBox.getHeight())/2 + 1
        # if self.config.margin is not None:
        #     if self.config.margin < margin:
        #         raise ValueError("margin is not large enough for PSF")
        # bboxI = exposure.getBBox(lsst.afw.image.PARENT)
        # bboxI.grow(-margin)
        # bboxD = lsst.afw.geom.BoxD(bboxI)
        
