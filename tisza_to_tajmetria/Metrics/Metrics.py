from enum import Enum

from .EffectiveMeshSize import EffectiveMeshSize
from .Euclidean import Euclidean
from .FractalDimensionIndex import FractalDimensionIndex
from .GreatestPatchArea import GreatestPatchArea
from .LandscapeDivision import LandscapeDivision
from .LandscapeProportion import LandscapeProportion
from .LandCover import LandCover


class Metrics(Enum):
    CalculateEffectiveMeshSize = (EffectiveMeshSize.name, EffectiveMeshSize.calculateMetric)
    CalculateEuclidean = (Euclidean.name, Euclidean.calculateMetric)
    FractalDimensionIndex = (FractalDimensionIndex.name, FractalDimensionIndex.calculateMetric)
    GreatestPatchArea = (GreatestPatchArea.name, GreatestPatchArea.calculateMetric)
    LandscapeDivision = (LandscapeDivision.name, LandscapeDivision.calculateMetric)
    LandscapeProportion = (LandscapeProportion.name, LandscapeProportion.calculateMetric)
    LandCover = (LandCover.name, LandCover.calculateMetric)

    def __init__(self, name: str, metric):
        self._name = name
        self.metric = metric

    @property
    def getMetricName(self):
        return self._name

    def getMetricCalculation(self):
        return self.metric