import os
import random
from typing import Tuple, List

from PIL import Image

from hc_logger import logging as log_utils

logger = log_utils.get_logger(os.path.basename(__file__))


class CornPlantAnalyzeResult(object):
    area_id: str
    plant_height: float
    leaf_angle: float
    ears_height: float

    def __init__(self,
                 area_id: str,
                 plant_height: float,
                 leaf_angle: float,
                 ears_height: float):
        self.area_id = area_id
        self.plant_height = plant_height
        self.leaf_angle = leaf_angle
        self.ears_height = ears_height


def calculate_nearest_small_cell(x,
                                 y,
                                 angle_deg):
    if 0 <= angle_deg < 90:
        nearest_column = chr(ord('A') + int(x))
        nearest_cell_y = int(y)
    elif 90 <= angle_deg < 180:
        nearest_column = chr(ord('A') + int(x))
        nearest_cell_y = int(y) + 1
    elif 180 <= angle_deg < 270:
        nearest_column = chr(ord('A') + int(x) - 1)
        nearest_cell_y = int(y) + 1
    else:
        nearest_column = chr(ord('A') + int(x) - 1)
        nearest_cell_y = int(y)

    return f'{nearest_column}{nearest_cell_y}'


def analyze_photo(photo_image: Image.Image,
                  longitude: float,
                  latitude: float,
                  orientation_angle: float) -> Tuple[bool, List[CornPlantAnalyzeResult]]:
    # todo 实现这个功能
    count = random.randint(1, 10)
    results = []
    for i in range(count):
        plant_height = random.uniform(1.8, 2.2)
        leaf_angle = random.uniform(30, 60)
        ears_height = random.uniform(0.2, 0.3)
        area_id = calculate_nearest_small_cell(x=longitude, y=latitude, angle_deg=orientation_angle)
        results.append(CornPlantAnalyzeResult(area_id=area_id, plant_height=plant_height, leaf_angle=leaf_angle,
                                              ears_height=ears_height))
    return True, results
