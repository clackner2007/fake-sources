
# fakePipe Test Using `hscPipe 4.0.1`

---- Song Huang 2016.01.05 ----

## Basic Information: 

    * Using `hscPipe 4.0.1`
    * Use data from: `/lustre/Subaru/SSP/rerun/DR_S16A`
    
    * Input catalog is based on Claire Lackner's Sersic model fit to HSC/ACS images of 
      galaxies in the COSMOS field.  
    * For now, only test using HSC-G, HSC-R and HSC-I bands.

--------

## Input Catalog of Fake Galaxies: 

### Galaxies as faint as 25.2 magnitudes

    * From Claire's fit to COSMOS galaxies, down to `F814W=25.2 mag`:
        - `ser_25.2_listarcsec.fits`
        - There are **86440** galaxies

    * Select the ones with reasonable properties, and suitable for fakePipe tests: 
      ```
      mag <= 25.2 && reff >= 0.05 && reff <= 5.0 && sersic_n >= 0.5 && sersic_n <= 4.5 
          && b_a >= 0.24 && b_a <= 0.99
      ```
      - This results in **46873** galaxies. 

    * There is a population of faint galaxies with very large `reff` 
        (when plotting `mag` againt `reff`).  Exclude them from the sample using: 
      ```
      mag <= 23.0 || reff <= (-0.25 * mag + 7.2)
      ```
      - This results in **46511** galaxies.
      - **Fig.1**: See `cosmos_mag_reff_cut.png`

    * Make a multiband catalog: 
        - `g-i` = 0.5 

    * Save the catalog: `cosmos_25.2_multiband.fits`

### Bright Galaxies (`mag <= 21.5`)

    * Other cuts are the same with the above catalog 
        - There are **2416** galaxies in the sample.

    * Save the catalog: `cosmos_21.5_multiband.fits`

### Basic Properties of the Sample

    1. Magnitude: **Fig.2**, see `cosmos_fake_mag.png` 
    2. Effective radius: **Fig.3**, see `cosmos_fake_reff.png` 
    3. Sersic index: **Fig.4**, see `cosmos_fake_sersicn.png` 
    3. Axis ratio: **Fig.5**, see `cosmos_fake_ba.png` 

----

## HSC Data

* Using the data from rerun: `DR_S16A`.
* 2 WIDE Tracts in the `XMM_LSS` field.

### Wide: Tract:8766 

#### Find Visits: 

    * Command:
    ``` bash
    tractFindVisits.py DR_S16A 8766 --filter='HSC-I'
    tractFindVisits.py DR_S16A 8766 --filter='HSC-R'
    tractFindVisits.py DR_S16A 8766 --filter='HSC-Z'
    tractFindVisits.py DR_S16A 8766 --filter='HSC-G'
    tractFindVisits.py DR_S16A 8766 --filter='HSC-Y'
    ```

    * Results: 

    ```
    # Input visits for Tract=8766 Filter=HSC-I
        # Input CCDs includes 28 Visits: 
    7288^7300^7304^7310^7318^7322^7338^7340^7344^7346^7352^7356^7358^7372^7384^7386^7408^19396^19400^19414^19416^19454^19456^19466^19468^19470^19482^19484 

    # Input visits for Tract=8766 Filter=HSC-G
        # Input CCDs includes 28 Visits:
9840^9852^9856^9862^9868^9870^9882^9886^9888^9898^9900^9912^9918^11568^11572^11578^11582^11586^11588^11596^11598^11640^42456^42460^42512^42514^42534^42536

    # Input visits for Tract=8766 Filter=HSC-R
        # Input CCDs includes 18 Visits:
11426^11442^11446^11468^11474^11476^11478^11498^11504^11506^11532^11534^41064^41068^41120^41122^41142^41144

    # Input visits for Tract=8766 Filter=HSC-Z
        # Input CCDs includes 28 Visits:
9696^9708^9712^9718^9724^9726^9730^9732^9736^9738^9744^9748^9750^9762^9772^9774^13288^17672^17676^17692^17694^17722^17724^17736^17738^17740^17750^17752

    # Input visits for Tract=8766 Filter=HSC-Y
        # Input CCDs includes 17 Visits
6466^6478^6482^6490^6496^6498^6522^6524^6528^6530^6538^6542^6544^6566^13152^13154^13198
    ```

### Show Visits

    * Command: 

    - HSC-I band
    ``` bash 
    showTractVisit.py /lustre/Subaru/SSP/rerun/DR_S16A 8766  7288^7300^7304^7310^7318^7322^7338^7340^7344^7346^7352^7356^7358^7372^7384^7386^7408^19396^19400^19414^19416^19454^19456^19466^19468^19470^19482^19484 -p 
    ```
        - See: `dr16a_8766_patches_HSC-I.png`

    - HSC-G band
    ``` bash 
    showTractVisit.py /lustre/Subaru/SSP/rerun/DR_S16A 8766  9840^9852^9856^9862^9868^9870^9882^9886^9888^9898^9900^9912^9918^11568^11572^11578^11582^11586^11588^11596^11598^11640^42456^42460^42512^42514^42534^42536 -p 
    ```
        - See: `dr16a_8766_patches_HSC-G.png`

    - HSC-R band
    ``` bash 
    showTractVisit.py /lustre/Subaru/SSP/rerun/DR_S16A 8766  11426^11442^11446^11468^11474^11476^11478^11498^11504^11506^11532^11534^41064^41068^41120^41122^41142^41144 -p 
    ```
        - See: `dr16a_8766_patches_HSC-R.png`


### Wide: Tract:8767 

#### Find Visits: 

    * Command:
    
    ``` bash
    tractFindVisits.py DR_S16A 8767 --filter='HSC-I'
    tractFindVisits.py DR_S16A 8767 --filter='HSC-R'
    tractFindVisits.py DR_S16A 8767 --filter='HSC-Z'
    tractFindVisits.py DR_S16A 8767 --filter='HSC-G'
    tractFindVisits.py DR_S16A 8767 --filter='HSC-Y'
    ```

    * Results: 

    ```
    # Input visits for Tract=8767 Filter=HSC-I
        # Input CCDs includes 26 Visits
7292^7296^7304^7308^7312^7318^7320^7322^7340^7342^7346^7348^7354^7358^7360^7374^7386^7388^19400^19404^19416^19418^19456^19470^19484^19486

    # Input visits for Tract=8767 Filter=HSC-G
        # Input CCDs includes 28 Visits
9844^9848^9856^9860^9870^9872^9884^9900^9902^9904^9906^9912^9914^11564^11572^11576^11584^11590^11598^11600^42460^42464^42468^42500^42514^42516^42536^42538

    # Input visits for Tract=8767 Filter=HSC-R
        # Input CCDs includes 19 Visits
11430^11434^11446^11450^11470^11478^11480^11500^11508^11534^11536^41068^41072^41076^41108^41122^41124^41144^41146

    # Input visits for Tract=8767 Filter=HSC-Z
        # Input CCDs includes 29 Visits
9700^9704^9712^9716^9720^9724^9726^9728^9732^9734^9738^9740^9746^9750^9752^9764^9774^9776^17676^17680^17694^17696^17724^17740^17752^17754^44638^44670^44680

    # Input visits for Tract=8767 Filter=HSC-Y
        # Input CCDs includes 20 Visits
6470^6474^6482^6486^6492^6496^6498^6500^6524^6526^6530^6532^6540^6544^6546^6568^13154^13156^44074^44084
    ```

### Show Visits

    * Command: 

    - HSC-I band
    ``` bash 
    showTractVisit.py /lustre/Subaru/SSP/rerun/DR_S16A 8767 7292^7296^7304^7308^7312^7318^7320^7322^7340^7342^7346^7348^7354^7358^7360^7374^7386^7388^19400^19404^19416^19418^19456^19470^19484^19486 -p 
    ```
        - See: `dr16a_8767_patches_HSC-I.png`

    - HSC-G band
    ``` bash 
    showTractVisit.py /lustre/Subaru/SSP/rerun/DR_S16A 8767 9844^9848^9856^9860^9870^9872^9884^9900^9902^9904^9906^9912^9914^11564^11572^11576^11584^11590^11598^11600^42460^42464^42468^42500^42514^42516^42536^42538 -p 
    ```
        - See: `dr16a_8767_patches_HSC-G.png`

    - HSC-R band
    ``` bash 
    showTractVisit.py /lustre/Subaru/SSP/rerun/DR_S16A 8767 11430^11434^11446^11450^11470^11478^11480^11500^11508^11534^11536^41068^41072^41076^41108^41122^41124^41144^41146 -p 
    ```
        - See: `dr16a_8767_patches_HSC-R.png`

### Generate the "Accept" masks for these two Tracts: 

    * **This is an optional step, and involves using code outside the fakePipe.**
      Please contact Song Huang if you want to generate these for your data.

    * Under `/lustre/Subaru/SSP/rerun/song/fake/dr_s16a`
        - Using `HSC-I` band as reference
        - `batchShapeComb.sh` and `dr16a_wide_fakeTest.lis`
        - Command: 
            ``` bash 
            ./batchShapeComb.sh dr16a_wide_fakeTest.lis
            ```
        - Results saved in `8766/shape` and `8767/shape`
        - The two accept masks are:
            1. `dr16a_wide_8766_HSC-I_shape_all.wkb`
            2. `dr16a_wide_8767_HSC-I_shape_all.wkb`

    * For these two Tracts, no Patch is missing, so the TractShape is very simple: 
        1. `dr16a_wide_8766_HSC-I_shape_all.png`
        2. `dr16a_wide_8767_HSC-I_shape_all.png`

### Generate the "Accept" masks for these two Tracts: 

    * **This is an optional step, and involves using code outside the fakePipe.**
      Please contact Song Huang if you want to generate these for your data.

    * Right now, the `BRIGHT_OBJECT` mask can be also combined; 
      But it is better to use the flag in the output catalog to exclude objects 
      contaminated by the bright stars. 

    * Under `/lustre/Subaru/SSP/rerun/song/fake/dr_s16a`
        - Using `HSC-I` band as reference
        - `batchNoData.sh` and `dr16a_wide_fakeTest.lis`
        - Command: 
            ``` bash 
            ./batchNoData.sh dr16a_wide_fakeTest.lis
            ```
        - Results saved in `8766/nodata` and `8767/nodata`
        - The mask files are: 
            1. `dr16a_wide_8766_HSC-I_nodata_big.wkb`
            2. `dr16a_wide_8766_HSC-I_shape_all.wkb`
            3. `dr16a_wide_8767_HSC-I_nodata_big.wkb`
            4. `dr16a_wide_8767_HSC-I_shape_all.wkb`

    * The visualizations of these masks are available here: 
        1. `dr16a_wide_8766_HSC-I_nodata_big.png`
        2. `dr16a_wide_8766_HSC-I_shape_all.png`
        3. `dr16a_wide_8767_HSC-I_nodata_big.png`
        4. `dr16a_wide_8767_HSC-I_shape_all.png`
    * **There is an extremely bright star that affect many Patches in Tract 8766**

---- 

## Generate Input Catalogs:

### For full catalog

#### Tract: 8766

    * Configuration:
        - Input: `cosmos_25.2_multiband.fits`
        - acpMask: `dr16a_wide_8766_HSC-I_shape_all.wkb`
        - rejMask: `dr16a_wide_8766_HSC-I_nodata_all.wkb`
        - Only add to innerTract, and rename the ID column 
        - Outputs: rename to `full_8766_radec_G/R/I/Z/Y.fits`

    * Command:
    ``` bash
    makeSourceList.py /lustre/Subaru/SSP \
         --rerun=DR_S16A \
         --id tract=8766 filter='HSC-I' patch='4,4' \
         -c inputCat='../cosmos_25.2_multiband.fits' \
         acpMask='dr16a_wide_8766_HSC-I_shape_all.wkb' \
         rejMask='dr16a_wide_8766_HSC-I_nodata_all.wkb' \
         rhoFakes=450 innerTract=True uniqueID=True
    ``` 

    * Results: 
        - **36119** galaxies are left in the catalog.
        - The RA,Dec distribution of the fake sources is: `full_8766_radec_I.png` 

#### Tract: 8767

    * Configuration:
        - Input: `cosmos_25.2_multiband.fits`
        - acpMask: `dr16a_wide_8767_HSC-I_shape_all.wkb`
        - rejMask: `dr16a_wide_8767_HSC-I_nodata_all.wkb`
        - Only add to innerTract, and rename the ID column 
        - Outputs: rename to `full_8767_radec_G/R/I/Z/Y.fits`

    * Command:
    ``` bash
    makeSourceList.py /lustre/Subaru/SSP \
         --rerun=DR_S16A \
         --id tract=8767 filter='HSC-I' patch='4,4' \
         -c inputCat='../cosmos_25.2_multiband.fits' \
         acpMask='dr16a_wide_8767_HSC-I_shape_all.wkb' \
         rejMask='dr16a_wide_8767_HSC-I_nodata_all.wkb' \
         rhoFakes=450 innerTract=True uniqueID=True
    ``` 

    * Results: 
        - **36237** galaxies are left in the catalog.
        - The RA,Dec distribution of the fake sources is: `full_8767_radec_I.png` 

### For bright galaxies: 

#### Tract: 8766

    * Configuration:
        - Input: `cosmos_21.5_multiband.fits`
        - acpMask: `dr16a_wide_8766_HSC-I_shape_all.wkb`
        - rejMask: `dr16a_wide_8766_HSC-I_nodata_big.wkb`
        - Only add to innerTract, and rename the ID column 
        - Outputs: rename to `bright_8766_radec_G/R/I/Z/Y.fits`

    * Command:
    ``` bash
    makeSourceList.py /lustre/Subaru/SSP \
         --rerun=DR_S16A \
         --id tract=8766 filter='HSC-I' patch='4,4' \
         -c inputCat='../cosmos_21.5_multiband.fits' \
         acpMask='dr16a_wide_8766_HSC-I_shape_all.wkb' \
         rejMask='dr16a_wide_8766_HSC-I_nodata_big.wkb' \
         rhoFakes=300 innerTract=True uniqueID=True
    ``` 

    * Results: 
        - **24081** galaxies are left in the catalog.
        - The RA,Dec distribution of the fake sources is: `bright_8766_radec_I.png`

#### Tract: 8767

    * Configuration:
        - Input: `cosmos_21.5_multiband.fits`
        - acpMask: `dr16a_wide_8767_HSC-I_shape_all.wkb`
        - rejMask: `dr16a_wide_8767_HSC-I_nodata_big.wkb`
        - Only add to innerTract, and rename the ID column 
        - Outputs: rename to `bright_8766_radec_G/R/I/Z/Y.fits`

    * Command:
    ``` bash
    makeSourceList.py /lustre/Subaru/SSP \
         --rerun=DR_S16A \
         --id tract=8767 filter='HSC-I' patch='4,4' \
         -c inputCat='../cosmos_21.5_multiband.fits' \
         acpMask='dr16a_wide_8767_HSC-I_shape_all.wkb' \
         rejMask='dr16a_wide_8767_HSC-I_nodata_big.wkb' \
         rhoFakes=300 innerTract=True uniqueID=True
    ``` 

    * Results: 
        - **24177** galaxies are left in the catalog.
        - The RA,Dec distribution of the fake sources is: `bright_8767_radec_I.png`

----

## fakePipe Test: 

### Setup the environment: 

    * Commands: 
        - One should adjust the directory according to their installation.

    ``` bash 
    # Setup HSC environment on Master:
    . /data1a/ana/products2014/eups/default/bin/setups.sh 
    
    # Setup hscPipe:
    setup -v hscPipe 4.0.1 

    # Setup the Astrometry catalog:
    setup -v -j astrometry_net_data ps1_pv1.2c

    # Setup the TMV library (Used by Galsim)
    setup -v -j -r /home/clackner/src/tmv0.72/ 

    # Setup the Galsim library (Used by fakePipe)
    setup -v -j -r /home/song/code/GalSim-1.3.0/ 

    # Setup the fakePipe
    setup -v -r /home/song/work/fakes 
    ```

----- 

### runAddFake.py

    * Add fake galaxies to single visits.
    * Under: `/lustre/Subaru/SSP/rerun/song/fake/dr_s16a/`

#### Tract=8766; Full catalog: `full_8766`

##### HSC-I: `add_i` 

    * Config file: `addfake_8766_i_full.config` 

    * Command: `42746.master` 
    ``` bash
    runAddFakes.py /lustre/Subaru/SSP/ \
        --rerun DR_S16A:song/fake/full_8766 \
        --id visit="7288^7300^7304^7310^7318^7322^7338^7340^7344^7346^7352^7356^7358^7372^7384^7386^7408^19396^19400^19414^19416^19454^19456^19466^19468^19470^19482^19484" \
        --clobber-config -C addfake_8766_i_full.config \
        --queue small --job add_i_8766_full --nodes 9 --procs 12
    ```

##### HSC-G: `add_g` 

    * Config file: `addfake_8766_g_full.config` 

    * Command: `42748.master` 
    ``` bash
    runAddFakes.py /lustre/Subaru/SSP/ \
        --rerun DR_S16A:song/fake/full_8766 \
        --id visit="9840^9852^9856^9862^9868^9870^9882^9886^9888^9898^9900^9912^9918^11568^11572^11578^11582^11586^11588^11596^11598^11640^42456^42460^42512^42514^42534^42536" \
        --clobber-config -C addfake_8766_g_full.config \
        --queue small --job add_g_8766_full --nodes 9 --procs 12
    ```

##### HSC-R: `add_r` 

    * Config file: `addfake_8766_r_full.config` 

    * Command: `42750.master` 
    ``` bash
    runAddFakes.py /lustre/Subaru/SSP/ \
        --rerun DR_S16A:song/fake/full_8766 \
        --id visit="11426^11442^11446^11468^11474^11476^11478^11498^11504^11506^11532^11534^41064^41068^41120^41122^41142^41144" \
        --clobber-config -C addfake_8766_r_full.config \
        --queue small --job add_r_8766_full --nodes 9 --procs 12
    ```


#### Tract-8767; Bright galaxies: `bright_8766`

##### HSC-I: `add_i` 

    * Config file: `addfake_8767_i_bright.config` 

    * Command: `42747.master` 
    ``` bash
    runAddFakes.py /lustre/Subaru/SSP/ \
        --rerun DR_S16A:song/fake/full_8767 \
        --id visit="7292^7296^7304^7308^7312^7318^7320^7322^7340^7342^7346^7348^7354^7358^7360^7374^7386^7388^19400^19404^19416^19418^19456^19470^19484^19486" \
        --clobber-config -C addfake_8767_i_bright.config \
        --queue small --job add_i_8767_bright --nodes 9 --procs 12
    ```

##### HSC-G: `add_g` 

    * Config file: `addfake_8767_g_bright.config` 

    * Command: `42749.master` 
    ``` bash
    runAddFakes.py /lustre/Subaru/SSP/ \
        --rerun DR_S16A:song/fake/full_8767 \
        --id visit="9844^9848^9856^9860^9870^9872^9884^9900^9902^9904^9906^9912^9914^11564^11572^11576^11584^11590^11598^11600^42460^42464^42468^42500^42514^42516^42536^42538" \
        --clobber-config -C addfake_8767_g_bright.config \
        --queue small --job add_g_8767_bright --nodes 9 --procs 12
    ```

##### HSC-R: `add_r` 

    * Config file: `addfake_8767_r_bright.config` 

    * Command: `42751.master` 
    ``` bash
    runAddFakes.py /lustre/Subaru/SSP/ \
        --rerun DR_S16A:song/fake/full_8767 \
        --id visit="11430^11434^11446^11450^11470^11478^11480^11500^11508^11534^11536^41068^41072^41076^41108^41122^41124^41144^41146" \
        --clobber-config -C addfake_8767_r_bright.config \
        --queue small --job add_r_8767_bright --nodes 9 --procs 12
    ```

----- 
