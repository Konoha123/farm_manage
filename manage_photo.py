import os
from typing import Optional

from PIL import Image

from database import tables
from hc_logger import logging as log_utils

logger = log_utils.get_logger(os.path.basename(__file__))

photo_base_dir = os.path.join(".", "photos")

os.makedirs(photo_base_dir, exist_ok=True)


def add_photo(photo: Image.Image,
              longitude: float,
              latitude: float,
              orientation_angle: float, ) -> bool:
    photo_id = tables.add_photo_info(longitude=longitude, latitude=latitude, orientation_angle=orientation_angle)
    if photo_id is None:
        return False
    photo_path = os.path.join(photo_base_dir, f"{photo_id}.jpg")
    photo.save(photo_path)
    return True


def get_photo_image(photo_id: int) -> Optional[Image.Image]:
    photo_path = os.path.join(photo_base_dir, f"{photo_id}.jpg")
    try:
        photo = Image.open(photo_path)
        return photo
    except Exception as e:
        logger.error(e)
        return None
