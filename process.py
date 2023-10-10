import os

from sqlalchemy import asc, null

import analyze
import manage_photo

from database import core as database_core
from database import tables

from hc_logger import logging as log_utils

logger = log_utils.get_logger(os.path.basename(__file__))


def process_all():
    count, raw_list = database_core.paged_find_and_count(query_model=tables.PhotoInfo,
                                                         cond=tables.PhotoInfo.analyzed_at == null(),
                                                         orders=[asc(tables.PhotoInfo.id)], page_size=0)
    analyzed_photo_count: int = 0
    produced_plant_count: int = 0
    if count == 0:
        logger.info(f"No photo to process")
        return analyzed_photo_count, produced_plant_count
    for photo_info in raw_list:
        photo_id = photo_info.id
        photo_image = manage_photo.get_photo_image(photo_id)
        if photo_image is None:
            logger.error(f"photo_image:{photo_id} not found")
            continue
        success, analyze_results = analyze.analyze_photo(photo_image, photo_info.longitude, photo_info.latitude,
                                                         photo_info.orientation_angle)
        if not success:
            logger.error(f"analyze_result:{photo_id} failed")
            continue
        analyzed_photo_count += 1
        for analyze_result in analyze_results:
            plant_id = tables.add_corn_plant_info(area_id=analyze_result.area_id, photo_id=photo_id,
                                                  plant_height=analyze_result.plant_height,
                                                  leaf_angle=analyze_result.leaf_angle,
                                                  ears_height=analyze_result.ears_height)
            if plant_id is None:
                logger.error(f"plant_id:{photo_id} failed")
                continue
            produced_plant_count += 1
        tables.mark_photo_info_analyzed(photo_id)
        logger.info(f"Analyze Done:{photo_id} success")
    return analyzed_photo_count, produced_plant_count
