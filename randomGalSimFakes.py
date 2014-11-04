import numpy as np

import lsst.afw.image
import lsst.afw.geom
import lsst.afw.math
import lsst.afw.cameraGeom
import lsst.pex.config
from lsst.pipe.tasks.fakes import FakeSourcesConfig, FakeSourcesTask


import makeFakeGalaxy as makeFake


class RandomGalSimFakesConfig(FakeSourcesConfig):
    galList = lsst.pex.config.Field(dtype=str, doc="catalog of galaxies to add")
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
        self.galData = np.loadtxt(self.config.galList, dtype={'names':['ID', 'mag', 'sersic_n',
                                                                       'reff_pix', 'b_a', 'pos_ang'],
                                                              'formats':[int, float, float,
                                                                         float, float, float]})


    def run(self, exposure, sources, background):

        self.log.info("Adding fake random galaxies")
        psf = exposure.getPsf()
        psfBBox = psf.computeImage().getBBox()
        minMargin =  max(psfBBox.getWidth(), psfBBox.getHeight())/2 + 1
        md = exposure.getMetadata()

        for igal, gal in enumerate(self.galData):
            flux = exposure.getCalib().getFlux(gal['mag'])
            
            #don't put the galaxy within 2Re or one PSF box of the edge
            #this would probably be better served by splitting up the psf convolution and
            #the image generation
            margin = max(int(gal['reff_pix']*2)+1, minMargin)
            bboxI = (exposure.getBBox(lsst.afw.image.PARENT))
            bboxI.grow(-margin)
            bboxD = lsst.afw.geom.BoxD(bboxI)
            x = self.rng.flat(bboxD.getMinX(), bboxD.getMaxX())
            y = self.rng.flat(bboxD.getMinY(), bboxD.getMaxY())
            #TODO: check for overlaps here and regenerate x,y if necessary
                       
            psfImage = psf.computeKernelImage(lsst.afw.geom.Point2D(x, y))
            galArray = makeFake.galSimFakeSersic(flux, gal['reff_pix'], gal['sersic_n'], 
                                                 gal['b_a'], gal['pos_ang'], psfImage.getArray())
            galImage = lsst.afw.image.ImageF(galArray.astype(np.float32))
            galBBox = galImage.getBBox()
                      
            #TODO: check for 1/2 pixel offsets
            galImage = lsst.afw.math.offsetImage(galImage, 
                                                 x - galBBox.getWidth()/2.0, y - galBBox.getHeight()/2.0,
                                                 'bilinear')
            
            detector = exposure.getDetector()
            ccd =  lsst.afw.cameraGeom.cast_Ccd(detector)
            amp = ccd.findAmp(lsst.afw.geom.Point2I(int(x), int(y)))
            gain = amp.getElectronicParams().getGain()
            #TODO: add noise to image, this is position dependent so should be done here
            varImage = lsst.afw.image.ImageF(galImage, True)
            varImage /= gain

            md.set("FAKE%d" % gal['ID'], "%.3f, %.3f" % (x, y))
            self.log.info("Adding fake at: %.1f,%.1f"% (x, y))

            galMaskedImage = lsst.afw.image.MaskedImageF(galImage, None, varImage)
            #TODO: set the mask
            galMaskedImage.getMask().set(self.bitmask)
            subMaskedImage = exposure.getMaskedImage().Factory(exposure.getMaskedImage(),
                                                               galMaskedImage.getBBox(lsst.afw.image.PARENT),
                                                               lsst.afw.image.PARENT)
            subMaskedImage += galMaskedImage
        
