import numpy as np

import lsst.afw.image
import lsst.afw.geom
import lsst.afw.math
import lsst.afw.cameraGeom
import lsst.pex.config
from lsst.pipe.tasks.fakes import FakeSourcesConfig, FakeSourcesTask
# SONG: Import pyfits or something else?
import pyfits as fits

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
        self.npRand = np.random.RandomState(self.config.seed)
        # SONG: Use FITS catalog as input; works for the test
        self.galData = fits.open(self.config.galList)[1].data
        #self.galData = np.loadtxt(self.config.galList, dtype={'names':['ID', 'mag', 'sersic_n',
        #                                                               'reff_pix', 'b_a', 'pos_ang'],
        #                                                      'formats':[int, float, float,
        #                                                                 float, float, float]})


    def run(self, exposure, sources, background):

        self.log.info("Adding fake random galaxies")
        psf = exposure.getPsf()
        psfBBox = psf.computeImage().getBBox()
        minMargin =  max(psfBBox.getWidth(), psfBBox.getHeight())/2 + 1
        md = exposure.getMetadata()
        expBBox = exposure.getBBox()

        for igal, gal in enumerate(self.galData):
            flux = exposure.getCalib().getFlux(gal['mag'])

            #don't put the galaxy within 4Re or one PSF box of the edge
            margin = max(int(gal['reff_pix']*4)+1, minMargin)
            bboxI = (exposure.getBBox(lsst.afw.image.PARENT))
            bboxI.grow(-margin)
            bboxD = lsst.afw.geom.BoxD(bboxI)
            x = self.rng.flat(bboxD.getMinX(), bboxD.getMaxX())
            y = self.rng.flat(bboxD.getMinY(), bboxD.getMaxY())
            #TODO: check for overlaps here and regenerate x,y if necessary

            psfImage = psf.computeKernelImage(lsst.afw.geom.Point2D(x, y))

            # SONG: 1) Now "parse" the numpy record gal into parameters
            #       Only works for single Sersic now
            #       2) Truncation is possible, but not perfect; Basically, the
            #       truncation in Sersic does not reduce the array size, just
            #       truncate the flux to zero at r_trunc; The workaround is to
            #       draw the object into an "Image" with the size we want
            #       [Can still be quite tricky if we want the flux to be accurate]
            trunc = 10.0  # trunc = 0 means no truncation, which is default
            tsize = trunc * float(gal['reff_pix'])
            #       3) If truncation is applied to galaxy with high Sersic
            #       index, better changes the drawMethod="fft" instead of
            #       "real_space", which turns out to be quite time-cosuming
            method = "auto"
            #       4) By default, returns a object without convolution
            galObj = makeFake.galSimFakeSersic(flux, gal, trunc=trunc,
                                               drawMethod=method)
            # Song: Get the psfArray as you want;
            psfArray = psfImage.getArray()
            #       Convert it into a GSObj; Normalization is optional now
            psfObj   = makeFake.arrayToGSObj(psfArray, norm=True)
            #       Do the convolution, and return a numpy array with the right
            #       size, using the appropriate method
            galArray = makeFake.galSimConvolve(galObj, psfObj, size=tsize,
                                               method=method)

            galImage = lsst.afw.image.ImageF(galArray.astype(np.float32))
            galBBox = galImage.getBBox()
            galImage = lsst.afw.math.offsetImage(galImage,
                                                 x - galBBox.getWidth()/2.0 + 0.5,
                                                 y - galBBox.getHeight()/2.0 + 0.5,
                                                 'lanczos3')

 
           #check that we're within the larger exposure, otherwise crop
            if expBBox.contains(galImage.getBBox(lsst.afw.image.PARENT)) is False:
                newBBox = galImage.getBBox(lsst.afw.image.PARENT)
                newBBox.clip(expBBox)
                galImage = galImage.Factory(galImage, newBBox, lsst.afw.image.PARENT)
                galBBox = newBBox

            detector = exposure.getDetector()
            ccd =  lsst.afw.cameraGeom.cast_Ccd(detector)
            amp = ccd.findAmp(lsst.afw.geom.Point2I(int(x), int(y)))
            gain = amp.getElectronicParams().getGain()
            #TODO: figure out an HSC way to do add the noise
            #TODO: this is gaussian noise right now, probably good enough
            varImage = lsst.afw.image.ImageF(galImage, True)
            varImage /= gain
            noiseArray = self.npRand.normal(loc=0.0, 
                                            scale=np.sqrt(np.abs(varImage.getArray())), 
                                             size=(galBBox.getHeight(),
                                                   galBBox.getWidth()))
            noiseImage = lsst.afw.image.ImageF(noiseArray.astype(np.float32))
            galImage += noiseImage

            md.set("FAKE%d" % gal['ID'], "%.3f, %.3f" % (x, y))
            self.log.info("Adding fake at: %.1f,%.1f"% (x, y))

            galMaskedImage = lsst.afw.image.MaskedImageF(galImage, None, varImage)
            #TODO: set the mask
            galMaskedImage.getMask().set(self.bitmask)
            subMaskedImage = exposure.getMaskedImage().Factory(exposure.getMaskedImage(),
                                                               galMaskedImage.getBBox(lsst.afw.image.PARENT),
                                                               lsst.afw.image.PARENT)
            subMaskedImage += galMaskedImage

