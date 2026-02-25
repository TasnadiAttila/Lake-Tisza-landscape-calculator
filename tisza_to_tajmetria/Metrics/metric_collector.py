from enum import Enum

from tisza_to_tajmetria.Metrics.MetricImplementations.effective_mesh_size import EffectiveMeshSize
from tisza_to_tajmetria.Metrics.MetricImplementations.euclidean import Euclidean
from tisza_to_tajmetria.Metrics.MetricImplementations.fractal_dimension_index import FractalDimensionIndex
from tisza_to_tajmetria.Metrics.MetricImplementations.greatest_patch_area import GreatestPatchArea
from tisza_to_tajmetria.Metrics.MetricImplementations.landscape_division import LandscapeDivision
from tisza_to_tajmetria.Metrics.MetricImplementations.landscape_proportion import LandscapeProportion
from tisza_to_tajmetria.Metrics.MetricImplementations.land_cover import LandCover
from tisza_to_tajmetria.Metrics.MetricImplementations.mean_patch_area import MeanPatchArea
from tisza_to_tajmetria.Metrics.MetricImplementations.median_patch_area import MedianPatchArea
from tisza_to_tajmetria.Metrics.MetricImplementations.nearest_neighbour_distance import NearestNeighbourDistance
from tisza_to_tajmetria.Metrics.MetricImplementations.number_of_patches import NumberOfPatches
from tisza_to_tajmetria.Metrics.MetricImplementations.patch_cohesion_index import PatchCohesionIndex
from tisza_to_tajmetria.Metrics.MetricImplementations.patch_density import PatchDensity
from tisza_to_tajmetria.Metrics.MetricImplementations.smallest_patch_area import SmallestPatchArea
from tisza_to_tajmetria.Metrics.MetricImplementations.splitting_index import SplittingIndex


class Metrics(Enum):
    CalculateEffectiveMeshSize = (EffectiveMeshSize.name, EffectiveMeshSize.calculate_metric)
    CalculateEuclidean = (Euclidean.name, Euclidean.calculate_metric)
    FractalDimensionIndex = (FractalDimensionIndex.name, FractalDimensionIndex.calculate_metric)
    GreatestPatchArea = (GreatestPatchArea.name, GreatestPatchArea.calculate_metric)
    LandscapeDivision = (LandscapeDivision.name, LandscapeDivision.calculate_metric)
    LandscapeProportion = (LandscapeProportion.name, LandscapeProportion.calculate_metric)
    LandCover = (LandCover.name, LandCover.calculate_metric)
    MeanPatchArea = (MeanPatchArea.name, MeanPatchArea.calculate_metric)
    MedianPatchArea = (MedianPatchArea.name, MedianPatchArea.calculate_metric)
    NearestNeighbourDistance = (NearestNeighbourDistance.name, NearestNeighbourDistance.calculate_metric)
    NumberOfPatches = (NumberOfPatches.name, NumberOfPatches.calculate_metric)
    PatchCohesionIndex = (PatchCohesionIndex.name, PatchCohesionIndex.calculate_metric)
    PatchDensity = (PatchDensity.name, PatchDensity.calculate_metric)
    SmallestPatchArea = (SmallestPatchArea.name, SmallestPatchArea.calculate_metric)
    SplittingIndex = (SplittingIndex.name, SplittingIndex.calculate_metric)

    def __init__(self, name: str, metric):
        self._name = name
        self.metric = metric

    @property
    def metric_name(self):
        return self._name

    def get_metric_calculation(self):
        return self.metric