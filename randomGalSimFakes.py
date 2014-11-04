import numpy as np

import lsst.afw.image
import lsst.afw.geom
import lsst.afw.math
import lsst.afw.cameraGeom
import lsst.pex.config
from lsst.pipe.tasks.fakes import FakeSourcesConfig, FakeSourcesTask

import makeFakeGalaxy as makeFake


class RandomGalSimFakesConfig(FakeSourcesConfig):
    galList = lsst.pex.config.Field(doc="catalog of galaxies to add")
    #margin = lsst.pex.config.Field(dtype=int, default=None, optional=True,
    #                               doc="Size of margin at edge that should not be added")
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
                                                              'reff_pix':float,
                                                              'b_a':float,
                                                              'pos_ang':float})


    def run(self, exposure, sources, background):

        self.log.info("Adding fake random galaxies")
        psf = exposure.getPsf()
        md = exposure.getMetadata()

        for igal, gal in enumerate(self.galData):
            flux = exposure.getCalib().getFlux(gal['mag'])
           
            psfImage = psf.computeKernelImage(lsst.afw.geom.Point2D(x, y))

            galArray = makeFake.galSimFakeSersic(flux, gal['reff_pix'], gal['sersic_n'], 
                                                 gal['b_a'], gal['pos_ang'], psfImage)
            galImage = lsst.afw.image.ImageF(galArray.astype(np.float32))
            galBBox = galImage.getBBox()
            
            #TODO: these are conservative margins so the whole image is included
            # we could make this smarter
            margin = max(galBBox.getWidth(), galBBox.getHeight())/2 + 1
            bboxI = (exposure.getBBox(lsst.afw.image.PARENT)).grow(-margin)
            bboxD = lsst.afw.geom.BoxD(bboxI)
            
            x = self.rng.flat(bboxD.getMinX(), bboxD.getMaxX())
            y = self.rng.flat(bboxD.getMinY(), bboxD.getMaxY())
            #TODO: check for overlaps here and regenerate x,y if necessary
            #TODO: check for 1/2 pixel offsets
            lsst.afw.math.offsetImage(galImage, x + galBBox.getWidth()/2.0, y + galBBox.getHeight()/2.0,
                                      'bilinear')
            
            detector = exposure.getDetector()
            amp = lsst.afw.cameraGeom.utils.findAmp(detector, detector.getId(), x, y)
            gain = amp.getElectronicParams().getGain()
            #TODO: add noise to image, this is position dependent so should be done here
            varImage = lsst.afw.image.Image(galImage)
            varImage /= gain

            md.set("FAKE%d" % i, "%.3f, %.3f" % (x, y))
            self.log.info("Adding fake at: %.1f,%.1f"% (x, y))

            galMaskedImage = lsst.afw.image.MaskedImageF(galImage, variance=varImage)
            #TODO: set the mask
            galMaskedImage.getMask().set(self.bitmask)
            subMaskedImage = exposure.getMaskedImage().Factory(exposure.getMaskedImage(),
                                                               galMaskedImage.getBBox(lsst.afw.image.PARENT),
                                                               lsst.afw.image.PARENT)
            subMaskedImage += galMaskedImage
        
