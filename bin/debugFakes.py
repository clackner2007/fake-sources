#!/usr/bin/env python

import numpy
import lsst.pipe.base  as pipeBase
import lsst.pex.config as pexConfig
import lsst.daf.persistence as dafPersist
import lsst.pipe.tasks.coaddBase as coaddBase
from lsst.pipe.tasks.fakes import DummyFakeSourcesTask
import lsst.afw.display.ds9 as ds9

class DebugFakesConfig(pexConfig.Config):
    coaddName = pexConfig.ChoiceField(
        dtype   = str,
        doc     = "Type of data to use",
        default = "deep",
        allowed = {"deep"   : "deepCoadd"}
        )
    fakes = pexConfig.ConfigurableField(
        target = DummyFakeSourcesTask,
        doc = "Injection of fake sources for test purposes (retarget to enable)"
    )

butlerTarget = "raw"
dataIdContainer  = {
    "raw":              pipeBase.DataIdContainer,
    "src":              pipeBase.DataIdContainer,
    "deepCoadd":        coaddBase.ExistingCoaddDataIdContainer,
    "deepCoadd_skyMap": coaddBase.ExistingCoaddDataIdContainer,
    "wcs":              coaddBase.ExistingCoaddDataIdContainer,
}
    
class DebugFakesTask(pipeBase.CmdLineTask):

    _DefaultName = "DebugFakes"
    ConfigClass  = DebugFakesConfig

    # we need to kill each of these methods so the users won't
    # mess with persisted configs and version info
    def _getConfigName(self):
        return None
    def _getEupsVersionsName(self):
        return None
    def _getMetadataName(self):
        return None

    @classmethod
    def _makeArgumentParser(cls):
        parser = pipeBase.ArgumentParser(name=cls._DefaultName)
        parser.add_id_argument("--id", butlerTarget, help="Data ID, e.g. --id tract=1234 patch=2,2",
                               ContainerClass=dataIdContainer[butlerTarget])
        return parser
    

    def __init__(self, **kwargs):
        pipeBase.CmdLineTask.__init__(self, **kwargs)
        self.makeSubtask("fakes")

    def run(self, dataRef, **kwargs):
        self.log.info("Processing %s" % (dataRef.dataId))
        exposure = dataRef.get('calexp', immediate=True)
        self.fakes.run(exposure, sources=None, background=None)
        dataRef.put(exposure, "calexp")
        return 0


if __name__ == '__main__':
    DebugFakesTask.parseAndRun()

    
