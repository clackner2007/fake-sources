import numpy as np

import lsst.afw.image
import lsst.afw.geom
import lsst.afw.math
import lsst.afw.cameraGeom
import lsst.pex.config


"""
Helper functions for making fake sources
"""


def addNoise(galImage, detector, x, y, rand_gen=None):
    """
    adds noise to the the image and returns a variance plane
    INPUT: image to add noise to
           detector where the image will be located, this sets the gain
           x,y position in detector (pixel coordinates)
    NOTE: this assumes float type images and will break if given doubles
    RETURN: a MaskedImageF with the image with additional noise and the variance plane
    giving the variance due to the object
    """
    
    ccd =  lsst.afw.cameraGeom.cast_Ccd(detector)
    amp = ccd.findAmp(lsst.afw.geom.Point2I(int(x), int(y)))
    gain = amp.getElectronicParams().getGain()
    #TODO: this is gaussian noise right now, probably good enough
    varImage = galImage.Factory(galImage, True)
    varImage /= gain
    if rand_gen is None:
        rand_gen = np.random
    noiseArray = rand_gen.normal(loc=0.0, 
                                 scale=np.sqrt(np.abs(varImage.getArray())) + 1e-12, 
                                 size=(galImage.getHeight(),
                                       galImage.getWidth()))
    noiseImage = lsst.afw.image.ImageF(noiseArray.astype(np.float32))
    galImage += noiseImage
    
    return lsst.afw.image.MaskedImageF(galImage, None, varImage)
    

