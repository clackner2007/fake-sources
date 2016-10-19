# SynPipe Test for HSC S16A Data Release 

---- 

* by Song Huang (Kavli-IPMU)

----

## Introduction 

* These are the basic photometric tests using `SynPipe` and `hscPipe` version 4.0.5, and 
  also for the technical paper for SynPipe.  
* We will test using synthetic point sources and galaxies in five bands and selected
  Tracts that represent good and bad seeing.  
* We will also test the half million QSO-like point sources from Ji-Jia. 

----

## Preparation 

### Data Storage: 

* The metadata and results are kept on Master@IPMU, under Song Huang's working directory:
    ```
    /lustre/Subaru/SSP/rerun/song/fake/synpipe
    ```

### Tract Selection: 

* We select Tract=`9699` in VVDS chunk as Tract with very good seeing: <0.449 arcsec>
* We select Tract=`8764` in XMM-LSS chunk as Tract with bad seeing: <0.700 arcsec>
* Ji-Jia selected Tract=`9693` for his test 

### Regions with Useful Data within the Tract:

* These are files that define the regions of useful data within each Tract in each band 
  that are generated using script by Song Huang.  
* File `synpipe_test_tract.lis` contains the IDs of these three Tracts.

* Command: 
    ```
    ./batchShapeComb.sh synpipe_test_tract.lis /lustre2/HSC_DR/dr1/s15b/data/s15b_wide HSC-G dr1_s16a 
    ./batchShapeComb.sh synpipe_test_tract.lis /lustre2/HSC_DR/dr1/s15b/data/s15b_wide HSC-R dr1_s16a 
    ./batchShapeComb.sh synpipe_test_tract.lis /lustre2/HSC_DR/dr1/s15b/data/s15b_wide HSC-I dr1_s16a 
    ./batchShapeComb.sh synpipe_test_tract.lis /lustre2/HSC_DR/dr1/s15b/data/s15b_wide HSC-Z dr1_s16a 
    ./batchShapeComb.sh synpipe_test_tract.lis /lustre2/HSC_DR/dr1/s15b/data/s15b_wide HSC-Y dr1_s16a 
    ```

* All the three Tracts are fully covered, not necessary to combine the region files for
  all five bands.

* Useful files, under `/lustre/Subaru/SSP/rerun/song/fake/synpipe/mask/`:
    ```
    dr1_s16a_9693_HSC-I_shape_all.wkb 
    dr1_s16a_9699_HSC-I_shape_all.wkb
    dr1_s16a_8764_HSC-I_shape_all.wkb
    ```

### Regions with Problematic Data: 

* These are files that define the regions with problematic pixels like the interpolated
  ones, and they are also generated using script by Song Huang. 

* Command:
    ```
    ./batchNoData.sh synpipe_test_tract.lis /lustre2/HSC_DR/dr1/s15b/data/s15b_wide HSC-G dr1_s16a 
    ./batchNoData.sh synpipe_test_tract.lis /lustre2/HSC_DR/dr1/s15b/data/s15b_wide HSC-R dr1_s16a 
    ./batchNoData.sh synpipe_test_tract.lis /lustre2/HSC_DR/dr1/s15b/data/s15b_wide HSC-I dr1_s16a 
    ./batchNoData.sh synpipe_test_tract.lis /lustre2/HSC_DR/dr1/s15b/data/s15b_wide HSC-Z dr1_s16a 
    ./batchNoData.sh synpipe_test_tract.lis /lustre2/HSC_DR/dr1/s15b/data/s15b_wide HSC-Y dr1_s16a 
    ```

* Combine the regions files in five bands together using function `combineWkbFiles()`
  under `coaddPatchNoData.py`

* Useful files, under `/lustre/Subaru/SSP/rerun/song/fake/synpipe/mask/`
    ```
    
    ```

### List of Visits that belong to each Tract: 

* Find all the Visits that are used to generate the coadd images in the Tract.  

* Using script within SynPipe. Example command: 
    ```
    tractFindVisits.py s15b_wide 9693 --filter='HSC-G' --dataDir='/lustre2/HSC_DR/dr1/s15b/data/'
    showTractVisit.py /lustre2/HSC_DR/dr1/s15b/data/s15b_wide 9693 6306^6322^6328^6334^6346^34334^34370^34380^34410^34428^34430^34452^38306^38310^38314^38316^38318^38324^38326^38330^38332^38342^38344^38346 -p
    ```

#### Tract=9693: 

* HSC-G: 24 visits
    ```
6306^6322^6328^6334^6346^34334^34370^34380^34410^34428^34430^34452^38306^38310^38314^38316^38318^38324^38326^38330^38332^38342^38344^38346
    ```

* HSC-R: 21 visits 
    ```
7124^7140^7146^7152^7164^11394^34636^34656^34668^34684^34694^34710^40754^40758^40762^40764^40766^40772^40774^40778^40780
    ```

* HSC-I: 33 visits 
    ```
14090^14094^35862^35874^35878^35888^35894^35896^35902^35908^35916^35922^35924^35926^35938^35940^35942^35952^35954^37978^37982^37986^37988^37990^37992^37994^37996^38000^38002^38008^38010^38014^38016
    ```

* HSC-Z: 33 visits 
    ```
9626^9684^9686^33890^33894^33904^33906^33908^33914^33916^33924^33926^33928^33930^33936^33938^33940^33946^33948^38878^38882^38886^38888^38890^38892^38894^38896^38900^38902^38908^38910^38914^38916
    ```

* HSC-Y: 33 visits 
    ```
13136^13138^34886^34888^34890^34892^34894^34896^34906^34908^34930^34932^34934^34936^36742^36764^36796^36814^36832^37522^37526^37530^37532^37534^37536^37538^37540^37544^37546^37552^37554^37558^37560
    ```

#### Tract=9699:

* HSC-G: 25 visits 
    ```
34358^34386^34388^34390^34392^34394^34396^34398^34416^34418^34420^34444^34446^38378^38382^38394^38414^38444^38446^38450^38452^38454^42144^42146^42156
    ```

* HSC-R: 25 visits 
    ```
34718^34722^34726^34730^34738^34740^34742^34744^34746^34752^34754^34756^34762^34768^34770^34774^34808^34812^34814^40788^40800^40806^40808^40812^40816
    ```

* HSC-I: 37 visits 
    ```
36122^36128^36132^36136^36152^36156^36160^36162^36164^36166^36168^36176^36178^36184^36186^36188^36190^36206^36208^36210^36220^36222^36232^36242^36244^36254^36256^36264^36266^38024^38044^38050^38052^38056^38060^38064^38068
    ```

* HSC-Z: 37 visits 
    ```
36430^38920^38924^38928^38930^38932^38934^38936^38938^38942^38946^38952^38956^38958^38962^38966^38970^38972^38974^38976^38978^38980^38984^38986^38988^38992^38994^38998^39000^39008^39016^39018^39020^39024^39028^44462^44466
    ```

* HSC-Y: 27 visits 
    ```
36734^36758^36760^36776^36826^36876^36878^36880^37564^37566^37570^37572^37574^37612^37624^37628^44010^44012^44014^44016^44020^44022^44024^44028^44030^44034^44036
    ```

#### Tract=8764: 

* HSC-G: 25 visits
    ```
11616^11624^11636^11640^11652^11654^11656^11674^15196^15214^15226^42428^42432^42448^42452^42472^42474^42498^42506^42508^42510^42520^42522^42530^42532
    ```

* HSC-R: 25 visits 
    ```
11418^11438^11464^11474^11492^11494^11502^11530^11550^11552^11554^41036^41040^41056^41060^41080^41082^41106^41114^41116^41118^41128^41130^41138^41140
    ```

* HSC-I: 37 visits 
    ```    
7398^7410^7412^7414^7416^7424^14134^14138^14148^14150^14168^14170^14180^14182^19388^19392^19408^19410^19412^19424^19426^19450^19452^19464^19466^19478^19480^45858^45862^45868^45870^45894^45896^45902^45904^45910^45912
    ```

* HSC-Z: 33 visits
    ```
9786^13278^13282^13286^13306^15080^15084^15086^15092^15098^15122^15134^15146^15158^17664^17668^17684^17686^17690^17702^17704^17718^17720^17734^17736^17746^17748^44630^44634^44648^44650^44676^44678
    ```

* HSC-Y: 37 visits 
    ```
6534^13184^13188^13196^13214^13216^13224^13226^13244^13254^16088^16094^16102^16110^39336^39356^39358^39360^39362^39364^39366^44092^44104^44110^44114^44120^44122^44126^44136^44142^44148^44150^44156^44158^44162^44164^44166
    ```

---- 

## Input Catalogs 

### Ji-Jia's QSO catalogs: 

* 500000 objects with magnitudes in all five bands: `jijia_qso_test.fits`

### Stars from S16A WIDE:

* 
