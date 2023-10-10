import datetime
import os
import time

import pydantic
from PIL import Image
from fastapi import FastAPI, Request, File, Form, UploadFile, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html, )
from fastapi.staticfiles import StaticFiles

import manage_photo
import process
from database import tables
from hc_logger import logging as log_utils

logger = log_utils.get_logger(os.path.basename(__file__))

# 初始化路由
app = FastAPI(title="玉米田地管理API", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory="static"), name="static")

origins = ["http://localhost.tiangolo.com", "https://localhost.tiangolo.com", "http://localhost",
           "http://localhost:8080", ]

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"],
                   allow_headers=["*"], )


# 增加swagger资源本地化中间件

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url=app.openapi_url, title=app.title + " - Swagger UI",
                               oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
                               swagger_js_url="/static/swagger-ui-bundle.js",
                               swagger_css_url="/static/swagger-ui.css", )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(openapi_url=app.openapi_url, title=app.title + " - ReDoc",
                          redoc_js_url="/static/redoc.standalone.js", )


# 增加时间测量中间件
@app.middleware("http")
async def add_process_time_header(request: Request,
                                  call_next):
    start_time = time.time()
    logger.info(f"开始处理请求：{request.url.include_query_params()}")
    response = await call_next(request)
    end_time = time.time()
    logger.info("处理结束，用时：{}毫秒".format(round(number=(end_time - start_time) * 1000, ndigits=2)))
    return response


class ServeStatus(pydantic.BaseModel):
    ok: bool
    description: str


photo_routers = APIRouter()


class UploadPhotoResponse(pydantic.BaseModel):
    status: ServeStatus


@photo_routers.post("/upload", response_model=UploadPhotoResponse, summary="上传照片", description="上传照片")
async def upload_photo(file: UploadFile = File(...),
                       longitude: float = Form(...),
                       latitude: float = Form(...),
                       orientation_angle: float = Form(...), ):
    try:
        logger.info("正在解析文件：{}".format(file.filename))
        img = Image.open(file.file).convert('RGB')
        success = manage_photo.add_photo(img, longitude, latitude, orientation_angle)
        if success:
            return UploadPhotoResponse(status=ServeStatus(ok=True, description="上传成功"))
        else:
            return UploadPhotoResponse(status=ServeStatus(ok=False, description="上传失败"))
    except Exception as e:
        logger.error(e)
        return UploadPhotoResponse(status=ServeStatus(ok=False, description="上传失败"))


class ClearAllPhotosResponse(pydantic.BaseModel):
    status: ServeStatus


@photo_routers.delete("/clear_all", response_model=ClearAllPhotosResponse, summary="清除所有照片",
                      description="清除所有照片")
async def clear_all_photos():
    try:
        success = manage_photo.clear_all_photos()
        if success:
            return ClearAllPhotosResponse(status=ServeStatus(ok=True, description="删除成功"))
        else:
            return ClearAllPhotosResponse(status=ServeStatus(ok=False, description="删除失败"))
    except Exception as e:
        logger.error(e)
        return ClearAllPhotosResponse(status=ServeStatus(ok=False, description="删除失败"))


class StatPhotoCountResponse(pydantic.BaseModel):
    status: ServeStatus
    analyzed_photo_count: int
    not_analyzed_photo_count: int


@photo_routers.get("/count_analyzed", response_model=StatPhotoCountResponse, summary="按照是否分析统计照片数量",
                   description="按照是否分析统计照片数量")
async def stat_photo_count():
    success, analyzed_photo_count, not_analyzed_photo_count = tables.stat_photo_info()
    if not success:
        return StatPhotoCountResponse(status=ServeStatus(ok=False, description="统计失败"))
    else:
        return StatPhotoCountResponse(status=ServeStatus(ok=True, description="统计成功"),
                                      analyzed_photo_count=analyzed_photo_count,
                                      not_analyzed_photo_count=not_analyzed_photo_count)


analyze_routers = APIRouter()


class ProcessAllUploadedPhotosResponse(pydantic.BaseModel):
    status: ServeStatus
    analyzed_photo_count: int
    produced_plant_count: int


@analyze_routers.put("/process_all", response_model=ProcessAllUploadedPhotosResponse, summary="处理所有上传的照片",
                     description="处理所有上传的照片")
async def process_all_uploaded_photos():
    analyzed_photo_count, produced_plant_count = process.process_all()
    return ProcessAllUploadedPhotosResponse(status=ServeStatus(ok=True, description="处理完毕"),
                                            analyzed_photo_count=analyzed_photo_count,
                                            produced_plant_count=produced_plant_count)


class CornPlantInfo(pydantic.BaseModel):
    corn_plant_id: int
    area_id: str
    photo_id: int
    plant_height: float
    leaf_angle: float
    ears_height: float
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ListAllCornPlantInfoResponse(pydantic.BaseModel):
    status: ServeStatus
    count: int
    results: list[CornPlantInfo]


@analyze_routers.get("/corn_plants/list_all", response_model=ListAllCornPlantInfoResponse,
                     summary="获取所有玉米植株信息", description="获取所有玉米植株信息")
async def list_all_corn_plants_info():
    success, count, corn_plants = tables.list_all_corn_plants_info()
    if not success:
        return ListAllCornPlantInfoResponse(status=ServeStatus(ok=False, description="获取失败"), count=0, results=[])
    results = [CornPlantInfo(area_id=result.area_id, photo_id=result.photo_id, plant_height=result.plant_height,
                             leaf_angle=result.leaf_angle, ears_height=result.ears_height,
                             corn_plant_id=result.corn_plant_id, created_at=result.created_at,
                             updated_at=result.updated_at) for result in corn_plants]
    return ListAllCornPlantInfoResponse(status=ServeStatus(ok=True, description="获取成功"), count=count,
                                        results=results)


class StatCornPlantInfoResult(pydantic.BaseModel):
    area_id: str
    plant_height_avg: float
    leaf_angle_avg: float
    ears_height_avg: float


class GetStatResultOfAllAreasResponse(pydantic.BaseModel):
    status: ServeStatus
    results: list[StatCornPlantInfoResult]


@analyze_routers.get("/stat_by_area", response_model=GetStatResultOfAllAreasResponse, summary="按小区统计",
                     description="按小区统计")
async def get_stat_result_of_all_areas():
    try:
        success, results = tables.stat_corn_plant_info_by_area_id()
        if success:
            return GetStatResultOfAllAreasResponse(status=ServeStatus(ok=True, description="获取成功"), results=[
                StatCornPlantInfoResult(area_id=result.area_id, plant_height_avg=result.plant_height_avg,
                                        leaf_angle_avg=result.leaf_angle_avg, ears_height_avg=result.ears_height_avg)
                for result in results])
        else:
            return GetStatResultOfAllAreasResponse(status=ServeStatus(ok=False, description="获取失败"), results=[])
    except Exception as e:
        logger.error(e)
        return GetStatResultOfAllAreasResponse(status=ServeStatus(ok=False, description="获取失败"), results=[])


app.include_router(photo_routers, prefix="/photos", tags=["照片管理"], )
app.include_router(analyze_routers, prefix="/analyze", tags=["分析管理"], )
