from enum import Enum

from tisza_to_tajmetria.Metrics.MetricImplementations.EffectiveMeshSize import EffectiveMeshSize
from tisza_to_tajmetria.Metrics.MetricImplementations.Euclidean import Euclidean
from tisza_to_tajmetria.Metrics.MetricImplementations.FractalDimensionIndex import FractalDimensionIndex
from tisza_to_tajmetria.Metrics.MetricImplementations.GreatestPatchArea import GreatestPatchArea
from tisza_to_tajmetria.Metrics.MetricImplementations.LandscapeDivision import LandscapeDivision
from tisza_to_tajmetria.Metrics.MetricImplementations.LandscapeProportion import LandscapeProportion
from tisza_to_tajmetria.Metrics.MetricImplementations.LandCover import LandCover
from tisza_to_tajmetria.Metrics.MetricImplementations.MeanPatchArea import MeanPatchArea


class Metrics(Enum):
    CalculateEffectiveMeshSize = (EffectiveMeshSize.name, EffectiveMeshSize.calculateMetric)
    CalculateEuclidean = (Euclidean.name, Euclidean.calculateMetric)
    FractalDimensionIndex = (FractalDimensionIndex.name, FractalDimensionIndex.calculateMetric)
    GreatestPatchArea = (GreatestPatchArea.name, GreatestPatchArea.calculateMetric)
    LandscapeDivision = (LandscapeDivision.name, LandscapeDivision.calculateMetric)
    LandscapeProportion = (LandscapeProportion.name, LandscapeProportion.calculateMetric)
    LandCover = (LandCover.name, LandCover.calculateMetric)
    MeanPatchArea = (MeanPatchArea.name, MeanPatchArea.calculateMetric)

    def __init__(self, name: str, metric):
        self._name = name
        self.metric = metric

    @property
    def getMetricName(self):
        return self._name

    def getMetricCalculation(self):
        return self.metric