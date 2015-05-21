import sys
import math
import collections

import lsst.afw.cameraGeom as afwCg
import hsc.pipe.base.butler as hscButler
from lsst.pipe.base import Struct, ArgumentParser
import lsst.pex.config
from hsc.pipe.base.pool import abortOnError, NODE, Pool, Debugger
from hsc.pipe.base.parallel import BatchPoolTask

from lsst.pipe.tasks.fakes import DummyFakeSourcesTask

Debugger().enabled = True

class addFakesConfig(lsst.pex.config.Config):
    fakes = lsst.pex.config.ConfigurableField(
        target = DummyFakeSourcesTask,
        doc = "Injection of fake sources into processed visits (retarget to enable)"
    )
    ignoreCcdList =lsst.pex.config.ListField(dtype=int, default=[], 
                                             doc="List of CCDs to ignore when processing")

class addFakesTask(BatchPoolTask):
    """Add fakes to entire exposure at once"""

    RunnerClass=hscButler.ButlerTaskRunner
    ConfigClass = addFakesConfig
    _DefaultName = "AddFakes"
    
    # we need to kill each of these methods so the users won't
    # mess with persisted configs and version info
    def _getConfigName(self):
        return None
    def _getEupsVersionsName(self):
        return None
    def _getMetadataName(self):
        return None

    def __init__(self, *args, **kwargs):
        """Constructor
        calls BatchPoolTask construtor, and setups up fakes subTask
        """
        super(addFakesTask, self).__init__(*args, **kwargs)
        self.makeSubtask("fakes")
        
    @classmethod
    def batchWallTime(cls, time, parsedCmd, numNodes, numProcs):
        """
        over-ridden method that gives the requested wall time for the method
        Probably not necessary here as this task is fast
        """
        numCcds = sum(1 for raft in parsedCmd.butler.get("camera") 
                      for ccd in afwCg.cast_Raft(raft))
        numCycles = int(math.ceil(numCcds/float(numNodes*numProcs)))
        numExps = len(cls.RunnerClass.getTargetList(parsedCmd))
        return time*numExps*numCycles

    @classmethod
    def _makeArgumentParser(cls, *args, **kwargs):
        """
        makes the argument parser.
        this task won't work for tracts/patches as it's currently written
        """
        doBatch = kwargs.pop("doBatch", False)
        parser = ArgumentParser(name=cls._DefaultName, *args, **kwargs)
        parser.add_id_argument("--id", datasetType="raw", level="visit",
                               help="data ID, e.g. --id visit=12345")
        return parser

    @abortOnError
    def run(self, expRef, butler):
        """
        sets up the pool and scatters the processing of the individual CCDs,
        
        in processCcd, apparently all nodes (master and slaves) run this
        method, but I don't really get that
        
        on the gather, we just check that any of the sources ran
        """
        
        pool = Pool(self._DefaultName)
        pool.cacheClear()
        pool.storeSet(butler=butler)
        
        dataIdList = dict([(ccdRef.get("ccdExposureId"), ccdRef.dataId)
                           for ccdRef in expRef.subItems("ccd") if 
                           ccdRef.datasetExists("raw")])
        dataIdList = collections.OrderedDict(sorted(dataIdList.items()))

        # Scatter: process CCDs independently
        outList = pool.map(self.process, dataIdList.values())
        numGood = sum(1 for s in outList if s==0)
        if numGood == 0:
            self.log.warn("All CCDs in exposure failed")
            return

    def process(self, cache, dataId):
        """
        add fakes to individual CCDs
        return None if we are skipping the CCD
        """
        cache.result = None
        if (dataId["ccd"] in self.config.ignoreCcdList) or (dataId['ccd'] > 103):
            self.log.warn("Ignoring %s: CCD in ignoreCcdList" % (dataId,))
            return None
        dataRef = hscButler.getDataRef(cache.butler, dataId)
        
        ccdId = dataRef.get("ccdExposureId")
        with self.logOperation("processing %s (ccdId=%d)" %(dataId, ccdId)):
            exposure = dataRef.get('calexp', immediate=True)
            self.fakes.run(exposure,None)
            dataRef.put(exposure,"calexp")
            
        return 0

