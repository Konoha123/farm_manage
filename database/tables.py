import datetime
import os
from typing import Optional, List, Tuple

from sqlalchemy import Column, String, Float, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func, null, distinct

from hc_logger import logging as log_utils
from . import core

logger = log_utils.get_logger(os.path.basename(__file__))


class PhotoInfo(core.Base):
    __tablename__ = 'photo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    longitude = Column("longitude", Float)
    latitude = Column("latitude", Float)
    orientation_angle = Column("orientation_angle", Float)
    analyzed_at = Column(DateTime, default=None)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class CornPlantInfo(core.Base):
    __tablename__ = 'corn_plant'
    id = Column(Integer, primary_key=True, autoincrement=True)
    area_id = Column("area_id", String(100))
    photo_id = Column("photo_id", Integer, ForeignKey('photo.id', ondelete="CASCADE"))
    plant_height = Column("plant_height", Float)
    leaf_angle = Column("leaf_angle", Float)
    ears_height = Column("ears_height", Float)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


def add_photo_info(longitude: float,
                   latitude: float,
                   orientation_angle: float) -> Optional[int]:
    photo_info = PhotoInfo(longitude=longitude, latitude=latitude, orientation_angle=orientation_angle)
    with core.dbEngine.locker:
        try:
            session = core.dbEngine.new_session()
        except Exception as e:
            logger.error(e)
            return None
        try:
            session.add(photo_info)
            session.commit()
            return photo_info.id
        except Exception as e:
            logger.error(e)
            return None
        finally:
            session.close()


def add_corn_plant_info(area_id: str,
                        photo_id: int,
                        plant_height: float,
                        leaf_angle: float,
                        ears_height: float) -> Optional[int]:
    corn_plant_info = CornPlantInfo(area_id=area_id, photo_id=photo_id, plant_height=plant_height,
                                    leaf_angle=leaf_angle, ears_height=ears_height)
    with core.dbEngine.locker:
        try:
            session = core.dbEngine.new_session()
        except Exception as e:
            logger.error(e)
            return None
        try:
            session.add(corn_plant_info)
            session.commit()
            return corn_plant_info.id
        except Exception as e:
            logger.error(e)
            return None
        finally:
            session.close()


def get_photo_info(photo_id: int) -> Optional[PhotoInfo]:
    with core.dbEngine.locker:
        try:
            session = core.dbEngine.new_session()
        except Exception as e:
            logger.error(e)
            return None
        try:
            photo_info = session.query(PhotoInfo).filter(PhotoInfo.id == photo_id).first()
            return photo_info
        except Exception as e:
            logger.error(e)
            return None
        finally:
            session.close()


def mark_photo_info_analyzed(photo_id: int) -> bool:
    with core.dbEngine.locker:
        try:
            session = core.dbEngine.new_session()
        except Exception as e:
            logger.error(e)
            return False
        try:
            photo_info = session.query(PhotoInfo).filter(PhotoInfo.id == photo_id).first()
            if photo_info is None:
                return False
            photo_info.analyzed_at = datetime.datetime.now()
            session.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False
        finally:
            session.close()


def clear_all_photo_info() -> bool:
    with core.dbEngine.locker:
        try:
            session = core.dbEngine.new_session()
        except Exception as e:
            logger.error(e)
            return False
        try:
            session.query(PhotoInfo).delete()
            session.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False
        finally:
            session.close()


def stat_photo_info() -> Tuple[bool, int, int]:
    try:
        analyze_photo_count, _ = core.paged_find_and_count(query_model=PhotoInfo, cond=PhotoInfo.analyzed_at != null(),
                                                           orders=[None], page_size=0)
        not_analyzed_photo_count, _ = core.paged_find_and_count(query_model=PhotoInfo,
                                                                cond=PhotoInfo.analyzed_at == null(), orders=[None],
                                                                page_size=0)
        return True, analyze_photo_count, not_analyzed_photo_count
    except Exception as e:
        logger.error(e)
        return False, 0, 0


class StatCornPlantInfoResult(object):
    area_id: str
    plant_height_avg: float
    leaf_angle_avg: float
    ears_height_avg: float

    def __init__(self,
                 area_id: str,
                 plant_height_avg: float,
                 leaf_angle_avg: float,
                 ears_height_avg: float):
        self.area_id = area_id
        self.plant_height_avg = plant_height_avg
        self.leaf_angle_avg = leaf_angle_avg
        self.ears_height_avg = ears_height_avg


def stat_corn_plant_info_by_area_id() -> Tuple[bool, List[StatCornPlantInfoResult]]:
    with core.dbEngine.locker:
        try:
            session = core.dbEngine.new_session()
        except Exception as e:
            logger.error(e)
            return False, []
        try:
            qry = session.query(CornPlantInfo.area_id, func.avg(CornPlantInfo.plant_height).label('plant_height_avg'),
                                func.avg(CornPlantInfo.leaf_angle).label('leaf_angle_avg'),
                                func.avg(CornPlantInfo.ears_height).label('ears_height_avg'))
            qry = qry.group_by(CornPlantInfo.area_id)
            results = qry.all()
            stat_result: List[StatCornPlantInfoResult] = [
                StatCornPlantInfoResult(area_id=result[0], plant_height_avg=result[1], leaf_angle_avg=result[2],
                                        ears_height_avg=result[3]) for result in results]
            return True, stat_result
        except Exception as e:
            logger.error(e)
            return False, []
        finally:
            session.close()


class CornPlantInfoResult(object):
    corn_plant_id: int
    area_id: str
    photo_id: int
    plant_height: float
    leaf_angle: float
    ears_height: float
    created_at: datetime.datetime
    updated_at: datetime.datetime

    def __init__(self,
                 corn_plant_id: int,
                 area_id: str,
                 photo_id: int,
                 plant_height: float,
                 leaf_angle: float,
                 ears_height: float,
                 created_at: datetime.datetime,
                 updated_at: datetime.datetime):
        self.corn_plant_id: int = corn_plant_id
        self.area_id: str = area_id
        self.photo_id: int = photo_id
        self.plant_height: float = plant_height
        self.leaf_angle: float = leaf_angle
        self.ears_height: float = ears_height
        self.created_at: datetime.datetime = created_at
        self.updated_at: datetime.datetime = updated_at


def list_all_corn_plants_info() -> Tuple[bool, int, List[CornPlantInfoResult]]:
    try:
        count, results = core.paged_find_and_count(query_model=CornPlantInfo, cond=None, orders=[], page_size=0)
        corn_plants = [
            CornPlantInfoResult(area_id=result.area_id, photo_id=result.photo_id, plant_height=result.plant_height,
                                leaf_angle=result.leaf_angle, ears_height=result.ears_height, corn_plant_id=result.id,
                                created_at=result.created_at, updated_at=result.updated_at) for result in results]
        return True, count, corn_plants
    except Exception as e:
        logger.error(e)
        return False, 0, []


class PhotoInfoResult(object):
    photo_id: int
    longitude: float
    latitude: float
    orientation_angle: float
    analyzed_at: datetime.datetime
    created_at: datetime.datetime
    updated_at: datetime.datetime

    def __init__(self,
                 photo_id: int,
                 longitude: float,
                 latitude: float,
                 orientation_angle: float,
                 analyzed_at: datetime.datetime,
                 created_at: datetime.datetime,
                 updated_at: datetime.datetime):
        self.photo_id: int = photo_id
        self.longitude: float = longitude
        self.latitude: float = latitude
        self.orientation_angle: float = orientation_angle
        self.analyzed_at: datetime.datetime = analyzed_at
        self.created_at: datetime.datetime = created_at
        self.updated_at: datetime.datetime = updated_at


def list_photo_info_by_area_id(area_id: str) -> Tuple[bool, int, List[PhotoInfoResult]]:
    try:
        session = core.dbEngine.new_session()
    except Exception as e:
        logger.error(e)
        return False, 0, []
    try:
        query = session.query(distinct(PhotoInfo.id), PhotoInfo)
        query = query.join(CornPlantInfo, CornPlantInfo.photo_id == PhotoInfo.id)
        query = query.filter(CornPlantInfo.area_id == area_id)
        query_results = query.all()
        results: List[PhotoInfoResult] = []
        for query_result in query_results:
            photo_info = query_result[1]
            results.append(
                PhotoInfoResult(photo_id=photo_info.id, longitude=photo_info.longitude, latitude=photo_info.latitude,
                                orientation_angle=photo_info.orientation_angle, analyzed_at=photo_info.analyzed_at,
                                created_at=photo_info.created_at, updated_at=photo_info.updated_at))
        return True, len(results), results
    except Exception as e:
        logger.error(e)
        return False, 0, []
