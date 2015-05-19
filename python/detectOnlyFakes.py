import random
import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.afw.table as afwTable
import lsst.afw.image as afwImage
import lsst.meas.algorithms as measAlg
import lsst.afw.detection as afwDetect

class OnlyFakesDetectionConfig(measAlg.SourceDetectionConfig):
    pass

class OnlyFakesDetectionTask(measAlg.SourceDetectionTask):
    """This task serves culls the source list to sources which overlap with fakes"""

    ConfigClass = OnlyFakesDetectionConfig

    def makeSourceCatalog(self, table, exposure, doSmooth=True, sigma=None, clearMask=True):
        if self.negativeFlagKey is not None and self.negativeFlagKey not in table.getSchema():
            raise ValueError("Table has incorrect Schema")

        # detect the footprints as usual
        fpSets = self.detectFootprints(exposure=exposure, doSmooth=doSmooth, sigma=sigma,
                                       clearMask=clearMask)

        mask = exposure.getMaskedImage().getMask()
        fakebit = mask.getPlaneBitMask('FAKE')
        fpPos = fpSets.positive.getFootprints()
        removes = []
        for i_foot, foot in enumerate(fpPos):
            footTmp = afwDetect.Footprint(foot)
            footTmp.intersectMask(mask, fakebit)
            if footTmp.getArea() == foot.getArea():
                removes.append(i_foot)
        removes = sorted(removes, reverse=True)
        for r in removes:
            del fpPos[r]

        fpSets.numPos = len(fpPos)
        if fpSets.negative:
            del fpSets.negative.getFootprints()[0:]
            fpSets.negative = None

        # make sources
        sources = afwTable.SourceCatalog(table)
        table.preallocate(fpSets.numPos)
        if fpSets.positive:
            fpSets.positive.makeSources(sources)

        return pipeBase.Struct(sources=sources, fpSets=fpSets)
