import os
import time

from fastapi import FastAPI, Request, File, Form, UploadFile
from fastapi.openapi.docs import (get_redoc_html, get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html, )
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from PIL import Image

import pydantic

from database import tables

from hc_logger import logging as log_utils

import manage_photo, process

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


class UploadPhotoResponse(pydantic.BaseModel):
    status: ServeStatus


@app.post("/upload_photo", tags=["照片管理"], response_model=UploadPhotoResponse, summary="上传照片",
          description="上传照片")
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


@app.delete("/clear_all_photos", tags=["照片管理"], response_model=ClearAllPhotosResponse, summary="清除所有照片",
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


class ProcessAllUploadedPhotosResponse(pydantic.BaseModel):
    status: ServeStatus


@app.put("/process_uploaded_photos", tags=["分析操作"], response_model=ProcessAllUploadedPhotosResponse,
         summary="处理所有上传的照片", description="处理所有上传的照片")
async def process_all_uploaded_photos():
    process.process_all()
    return ProcessAllUploadedPhotosResponse(status=ServeStatus(ok=True, description="处理完毕"))


class StatCornPlantInfoResult(pydantic.BaseModel):
    area_id: str
    plant_height_avg: float
    leaf_angle_avg: float
    ears_height_avg: float


class GetStatResultOfAllAreasResponse(pydantic.BaseModel):
    status: ServeStatus
    results: list[StatCornPlantInfoResult]


@app.get("/get_stat_result_of_all_areas", tags=["分析操作"], response_model=GetStatResultOfAllAreasResponse,
         summary="获取统计结果", description="获取统计结果")
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