from abc import ABC, abstractmethod

class IMetricsCalculator(ABC):

    name = None

    @staticmethod
    @abstractmethod
    def calculateMetric(layer):
        pass
