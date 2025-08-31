from enum import Enum

from .EffectiveMeshSize import EffectiveMeshSize
from .Euclidean import Euclidean

class Metrics(Enum):
    CalculateEffectiveMeshSize = (EffectiveMeshSize.name, EffectiveMeshSize.calculateMetric)
    CalculateEuclidean = (Euclidean.name, Euclidean.calculateMetric)

    def __init__(self, name: str, metric):
        self._name = name
        self.metric = metric

    @property
    def getMetricName(self):
        return self._name

    def getMetricCalculation(self):
        return self.metric