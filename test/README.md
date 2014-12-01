####Instructions for running test tasks
We've implemented three test cases for the the tasks below. You can run these to test that everything works and use them as templates for larger, more complicated tasks. 

###Adding stars at random positions
The task randomStarFakeSourcesTask adds fake stars of a given magnitude to an individual CCD at random positions. The sample configuration file is in `test/stars/config_star_test`. The available configuration parameters are:

name | description
---------| -------------
retarget | name of fake sources task to use
magnitude | magnitude of stars to add
nStars | number of stars to add ,default is 1
margin | size of margin around chip edge in which no sources should be added 
seed | seed for random generator 

The test case adds 100 stars of 22nd magnitude to visit 1236 and ccd 50 (COSMOS i-band data). To run the test, simply run `$ test_star_run.sh /path/to/data/ /path/to/rerun`. The example task then outputs a file `test_star_matchFakes.fits`, which is a list of the measurements of the fake stars. From here, you can check the PSF magnitudes of the stars against the input catalog. Note that because of the fixed random seed, galaxies will be added to the same pixel positions in all CCDs if you run this over multiple CCDs (i.e. using reduceFrames.py).

###Adding galaxies at given positions
The task randomGalFimFakes adds fake galaxies to random positions of a given CCD. The galaxies can be either Sersic or double Serisc profiles and a catalog of the galaxy properties are needed in a fits file. This is given to the config parameter `fakes.galList`. The input catalog needs to contain at least:
  1. ID (otherwise the index in the list is used)
  2. mag: desired total magnitude
  3. reff: half-light radius in arcseconds
  4. b_a: axis ratio
  5. theta: rotation angle, in degrees counter-clockwise from the x-axis
