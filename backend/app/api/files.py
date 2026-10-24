import os
import time
import uuid
import aiofiles
from pathlib import Path
from fastapi import APIRouter, File, Query, UploadFile

from app.common.exceptions import BusinessException
from app.common.response import Response
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR
from app.schemas.file import FileResponse

router = APIRouter(prefix="/files", tags=["文件管理"])


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    """文件上传接口"""

    if not file.filename:
        raise BusinessException(message="文件名不能为空")

    if file.size and file.size > MAX_FILE_SIZE:
        raise BusinessException(
            message=f"文件大小不能超过{MAX_FILE_SIZE // 1024 // 1024}MB"
        )

    original_name = os.path.basename(file.filename)
    ext = Path(original_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise BusinessException(message=f"不支持{ext}文件后缀")

    # 创建唯一文件名
    disk_name = f"{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}{ext}"
    save_path = UPLOAD_DIR / disk_name

    async with aiofiles.open(save_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            await f.write(chunk)

    return Response.success(
        message="文件写入成功",
        data=FileResponse(
            original_name=original_name,
            disk_name=disk_name,
            size=file.size,
            url=f"/uploads/{disk_name}",
        ),
    )
