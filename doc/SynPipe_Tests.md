# Summary of On-going SynPipe Tests 

* Last update: 2016/10/31

----- 

## Basic Photometric Tests for the SynPipe Paper: 

* by Song Huang @Kavli-IPMU (song.huang@ipmu.jp)

* The purpose of the tests is to provide basic photometric benchmarks of the current HSC 
  pipeline using synthetic stars and galaxies, to evaluate the accuracy of PSF, Kron, and 
  cModel photometry under ideal conditions.  

* All the catalogs are kept on `Master@IPMU`; Please contact Song Huang in case you are
  interested in them; The results will be used for the technical paper for SynPipe 

* The tests rightn now have three components: 

### Photometric Tests for Synthetic Stars
    - *Inputs*: 5-band photometry of real stars at $i < 26.5$ mag in the VVDs region.
        (Basic quality cuts applied)
    - **Tracts**: 9699 / 8764 
    - **Basic Information**: 5-band tests at single-visit level; 
        random locations within the Tract; 
        ~150000 stars per tract 
    - **Progress**: Finished 

### Photometric Tests for Synthetic Galaxies 
    - **Inputs**: Single Sersic model of COSMOS galaxies with $$i<25.2$$ mag from 
        Claire Lackner's catalog; Colors are based on multiband catalog for COSMOS
    - **Tracts**: 9699 / 8764 
    - **Basic Information**: 5-band tests at single-visit level; 
        random locations within the Tract; 
        ~60000-100000 galaxies per tract; 
        Will separate the galaxies into bright/faint subsamples at $$i\sim 23.0$$ mag.
    - **Progress**: In preparation

### Photometric Tests for Synthetic QSOs (On behalf of Ji-Jia)
    - **Inputs**: 5-band photometry of synthetic QSOs from Ji-Jia down to $$i > 28.0$$;
        QSOs are modeled as point sources. 
    - **Tracts**: 9693
    - **Basic Information**: 5-band tests at single-visit level; 
        random locations designed by Ji-Jia; 
        ~500000 QSOs per tract 
    - **Progress**: Finished 

