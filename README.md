This project is to add fake stellar and galaxy sources to the HSC data processing. 

####Setup
Currently, this is only enabled in a special version of processCcd.py. In order to get this code working at master.ipmu, you'll need to setup:
```bash
$ setup -v -r /home/bot/sandbox/bbot
$ setup -v -j astrometry_net_data ps1_pv1.2c
$ setup -v -j -r ~clackner/sandbox/ptas-bosch
$ setup -v -r path/to/fake-sources/
``` 

####Running
To run, you need to override the configure in the pipeline. The override is in config-random. You'll need to import the relevant file and then set retarget to the task you want to run. You can then set any other configurables here. The command to run it within the hsc pipeline is:
```bash
$ hscProcessCcd.py /to/data/ --rerun=/to/rerun --id visit=XXX ccd=YY -C config_random
```


