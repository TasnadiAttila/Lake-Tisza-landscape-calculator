from abc import ABC, abstractmethod

class IMetricsCalculator(ABC):

    name = None

    @staticmethod
    @abstractmethod
    def calculate_metric(layer):
        pass
