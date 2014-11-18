import numpy as np

import lsst.afw.image
import lsst.afw.geom
import lsst.afw.math
import lsst.afw.cameraGeom
import lsst.pex.config


"""
Helper functions for making fake sources
"""


def addNoise(galImage, detector, rand_gen=None):
    """
    adds noise to the the image and returns a variance plane
    INPUT: image to add noise to
           detector where the image will be located, this sets the gain
    NOTE: this assumes float type images and will break if given doubles
    RETURN: a MaskedImageF with the image with additional noise and the variance plane
    giving the variance due to the object
    """
    
    ccd =  lsst.afw.cameraGeom.cast_Ccd(detector)
    gainImage = galImage.Factory(galImage, True)
    gainImage.set(0.0)
    for ampId in (1,2,3,4):
        amp = ccd.findAmp(lsst.afw.cameraGeom.Id(ampId))
        ampBBox = amp.getDataSec()
        clippedBBox = gainImage.getBBox(lsst.afw.image.PARENT)
        clippedBBox.clip(ampBBox)
        if clippedBBox.getArea() > 0:
            tempImage = gainImage.Factory(gainImage, clippedBBox, lsst.afw.image.PARENT)
            tempImage.set(amp.getElectronicParams().getGain())
            del tempImage
        
    #TODO: this is gaussian noise right now, probably good enough
    varImage = galImage.Factory(galImage, True)
    varImage /= gainImage
    if rand_gen is None:
        rand_gen = np.random
    noiseArray = rand_gen.normal(loc=0.0, 
                                 scale=np.sqrt(np.abs(varImage.getArray())) + 1e-12, 
                                 size=(galImage.getHeight(),
                                       galImage.getWidth()))
    noiseImage = lsst.afw.image.ImageF(noiseArray.astype(np.float32))
    galImage += noiseImage
    
    return lsst.afw.image.MaskedImageF(galImage, None, varImage)
    

