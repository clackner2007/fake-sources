# File: makeFakeGalaxy.py

import numpy as np
import galsim

def arrayToGSObj(imgArr, scale=1.0, normalization='flux'):
    gsObj = galsim.InterpolatedImage(galsim.image.Image(imgArr), scale=scale,
                                     normalization=normalization)
    return gsObj

def plotFakeGalaxy(imgArr, galID=None):

    import matplotlib.pyplot as plt

    if galID is None:
        outPNG = 'fake_galaxy.png'
    else:
        outPNG = 'fake_galaxy_%i.png' % galID

    plt.figure(1, figsize=(8,8))
    plt.imshow(np.arcsinh(imgArr))
    plt.savefig(outPNG)

def galSimFakeSersic(flux, reffPix, nSersic, axisRatio, posAng, psfImage,
                     noConvole=False, addPoisson=False, scaleRad=False,
                     expAll=False, devAll=False, returnObj=False,
                     plotFake=False, galID=None):

    # Make sure Sersic index is not too large
    if nSersic > 6.0:
        raise ValueError("Sersic index is too large! Should be <= 6.0")
    # Check the axisRatio value
    if axisRatio <= 0.15:
        raise ValueError("Axis Ratio is too small! Should be >= 0.15")

    # Convert the PSF Image Array into a GalSim Object
    psfObj = arrayToGSObj(psfImage)

    # Make the Sersic model based on flux, re, and Sersic index
    if nSersic == 1.0 or expAll:
        if scaleRad:
            serObj = galsim.Exponential(scale_radius=reffPix, flux=flux)
        else:
            serObj = galsim.Exponential(half_light_radius=reffPix, flux=flux)
    elif nSersic == 4.0 or devAll:
        serObj = galsim.DeVaucouleurs(half_light_radius=reffPix, flux=flux)
    else:
        serObj = galsim.Sersic(nSersic, half_light_radius=reffPix, flux=flux)

    # If necessary, apply the Axis Ratio (q=b/a) using the Shear method
    if axisRatio < 1.0:
        serObj = serObj.shear(q=axisRatio, beta=0.0*galsim.degrees)
    # If necessary, apply the Position Angle (theta) using the Rotate method
    if posAng != 0.0 or posAng != 180.0:
        serObj = serObj.rotate(posAng*galsim.degrees)

    # Convolve the Sersic model using the provided PSF image
    # TODO: Make sure we understand the normalization
    if not noConvole:
        serFinal = galsim.Convolve([serObj, psfObj])
    else:
        serFinal = serObj

    # Generate an "Image" object for the convolved model
    serImg = serFinal.drawImage()

    # TODO: Should we add Possion noise at this point?
    if addPoisson:
        serImg.addNoise(galsim.PoissonNoise())

    # Return the Numpy array version of the image
    galArray = serImg.array

    # Make a PNG figure of the fake galaxy to check if everything is Ok
    # TODO: Should be removed later
    if plotFake:
        plotFakeGalaxy(galArray, galID=galID)

    if returnObj:
        return serFinal
    else:
        return galArray

def galSimFakeDoubleSersic(flux1, reffPix1, nSersic1, axisRatio1, posAng1,
                           flux2, reffPix2, nSersic2, axisRatio2, posAng2,
                           psfImage, noConvole=False, addPoisson=False,
                           plotFake=False, galID=None):

    serModel1 = galSimFakeSersic(flux1, reffPix1, nSersic1, axisRatio1, posAng1,
                                 psfImage, noConvole=True, returnObj=True)
    serModel2 = galSimFakeSersic(flux2, reffPix2, nSersic2, axisRatio2, posAng2,
                                 psfImage, noConvole=True, returnObj=True)
    serDouble = serModel1 + serModel2

    # Convert the PSF Image Array into a GalSim Object
    psfObj = arrayToGSObj(psfImage)

    # Convolve the Sersic model using the provided PSF image
    # TODO: Make sure we understand the normalization
    if not noConvole:
        serFinal = galsim.Convolve([serDouble, psfObj])
    else:
        serFinal = serDouble

    # Generate an "Image" object for the convolved model
    serImg = serFinal.drawImage()

    # TODO: Should we add Possion noise at this point?
    if addPoisson:
        serImg.addNoise(galsim.PoissonNoise())

    # Return the Numpy array version of the image
    galArray = serImg.array

    # Make a PNG figure of the fake galaxy to check if everything is Ok
    # TODO: Should be removed later
    if plotFake:
        plotFakeGalaxy(galArray, galID=galID)

    return galArray

def testMakeFake(galList):

    # Make a fake Gaussian PSF
    psfGaussian = galsim.Gaussian(fwhm=2.0)
    psfImage    = psfGaussian.drawImage().array

    galData = np.loadtxt(galList, dtype=[('ID','int'),
                                         ('mag','float'),
                                         ('sersic_n','float'),
                                         ('reff_pix','float'),
                                         ('b_a','float'),
                                         ('theta','float')])

    # Test SingleSersic
    for igal, gal in enumerate(galData):
        flux = 10.0 ** ((27.0 - gal['mag']) / 2.5)

        galArray = galSimFakeSersic(flux, gal['reff_pix'], gal['sersic_n'],
                                    gal['b_a'], gal['theta'], psfImage,
                                    plotFake=True, galID=gal["ID"])

        print galArray.shape

    # Test DoubleSersic
    flux1 = 10.0 ** ((27.0 - galData['mag'][0]) / 2.5)
    flux2 = 10.0 ** ((27.0 - galData['mag'][1]) / 2.5)
    re1, re2 = galData['reff_pix'][0], galData['reff_pix'][1]
    ns1, ns2 = galData['sersic_n'][0], galData['sersic_n'][1]
    ba1, ba2 = galData['b_a'][0], galData['b_a'][1]
    pa1, pa2 = galData['theta'][0], galData['theta'][1]

    doubleArray = galSimFakeDoubleSersic(flux1, re1, ns1, ba1, pa1,
                                         flux2, re2, ns2, ba2, pa2,
                                         psfImage, plotFake=True, galID=4)

    print doubleArray.shape

