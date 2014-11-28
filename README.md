This project is to add fake stellar and galaxy sources to the HSC data processing. 

####Setup
This code depends on the HSC pipeline (version 3.3.3 or later), and needs to have galsim built against the pipeline python. For some of the additional scripts (makeRaDec, matchFakes) the astropy package is also necessary. If you just have a list of sources however, you don't need it. This is already setup on master at IPMU, so if you are running there, you just need to setup the following:
In order to get this code working at master.ipmu, you'll need to setup:
```bash
$ export PYTHONPATH=/home/clackner/.local/lib/python2.7/site-packages:${PYTHONPATH}
$ setup -v -r hscPipe 3.3.3
$ setup -v -j astrometry_net_data ps1_pv1.2c
$ setup -v -r path/to/fake-sources/
``` 

####Running
To run, you need to override the default configuration in the pipeline to include fake sources. We have XX different tasks you can implement with the override config. They are:
  1. randomStarFakes: adds stars of a single brightness to random positions in a CCD
  2. randomGalSimFakes: adds galsim galaxies from a catalog to random positions in a CCD
  3. positionGalSimFakes: adds galsim galaxies from a catalog to fixed sky positions, also given in the catalog.
Examples of how to use these tasks and standard configurations are given in the test/stars and test/galaxies directories. The command to run these for a small set of CCDs would is:
```bash
$ hscProcessCcd.py /to/data/ --rerun=/to/rerun --id visit=XXX ccd=YY -C config_random
```

####*Debugging*
If you want to add check that the fake source adding is working without going through all the measurements, use debugFakes, which takes a calibrated exposure from a completed rerun (rerun1) and writes the exposure with fakes added to rerun2.
```bash
$ debugFakes.py /to/data/ --rerun=rerun1:rerun2 --id visit=XXX ccd=YY -C config_debug
```
Note that this will fail if rerun1 doesn't have the visit/ccd you are trying to process already in it.

####Make Random RA, DEC catalog 

* Right now, makeRaDecCat.py accepts either a dataId ({visit,ccd} or
  {tract,patch,filter}) or a range of {RA,Dec} as input. 
* To use it on single frame or coadd images, a rootDir for the data is also
  required 
* The rangeRaDec can be either a list or a numpy array in the format of 
  (raMin, raMax, decMin, decMax)
* The code will return a list of {RA,Dec} pairs; It also accepts an input fits
  catalog, and will add two columns to the catalog (RA, Dec).  Make sure the
  number of galaxies in the input catalog is equal or smaller than the number of
  random RA,Dec pairs (This can be improved later).  The output catalog will
  have a '_radec' suffix.  
* And, an optional 'rad' parameter is available as the minimum allowed
  separation (in unit of arcsec) between any of these random RA, Dec pairs. 

```python 
> rangeRaDec = [123.4, 123.8, 12.0, 13.0]
> inputCat = 'fakeExp.fits'
> randomRaDec = makeRaDecCat(50, rangeRaDec=rangeRaDec, rad=10.0, inputCat=inputCat)
```
or 

```python 
> dataId = {tract:0, patch:'4,5', filter:'HSC-I'}
> rootDir = '/lustre/Subaru/SSP/rerun/song/cosmos-i2' 
> inputCat = 'fakeExp.fits'
> randomRaDec = makeRaDecCat(50, dataId=dataId, rad=10.0, inputCat=inputCat,
>                            rootDir=rootDir)
```
