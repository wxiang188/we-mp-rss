from fastapi import APIRouter, Depends, HTTPException,Body,Path,Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from core.models.config_management import ConfigManagement
from core.db  import DB
from core.auth import get_current_user_or_ak
from .base import  success_response, error_response
from core.config import cfg
router = APIRouter(prefix="/configs", tags=["配置管理"])


@router.get("",summary="获取配置项列表")
def list_configs(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user_or_ak)
):
    """获取配置项列表 (合并 DB 和 YAML 数据)"""
    try:
        db = DB.get_session()
        # 1. 获取 YAML 中的初始配置
        from core.yaml_db import YamlDB
        yaml_configs = YamlDB.store_config_to_list(cfg._config)
        # 注意: YamlDB.store_config_to_list 返回的是模型对象列表，需要用 . 访问属性并转为字典
        configs_dict = {item.config_key: {
            "config_key": item.config_key,
            "config_value": item.config_value,
            "description": item.description or "系统配置项"
        } for item in yaml_configs}

        # 2. 获取数据库中的配置并覆盖 YAML 中的值
        db_configs = db.query(ConfigManagement).all()
        for db_cfg in db_configs:
            configs_dict[db_cfg.config_key] = {
                "config_key": db_cfg.config_key,
                "config_value": db_cfg.config_value,
                "description": db_cfg.description or "数据库配置项"
            }

        # 3. 转换为列表并分页
        all_configs = list(configs_dict.values())
        total = len(all_configs)
        # 简单排序以保持一致性
        all_configs.sort(key=lambda x: x["config_key"])
        
        paged_configs = all_configs[offset : offset + limit]

        return success_response(data={
            "list": paged_configs,
            "page": {
                "limit": limit,
                "offset": offset
            },
            "total": total
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return error_response(code=500, message=str(e))

@router.get("/{config_key}", summary="获取单个配置项详情")
def get_config(
    config_key: str,
    current_user: dict = Depends(get_current_user_or_ak)
):
    db=DB.get_session()
    """获取单个配置项详情"""
    try:
        config = db.query(ConfigManagement).filter(ConfigManagement.config_key == config_key).first()
        if not config:
            raise HTTPException(status_code=404, detail="Config not found")
        return success_response(data={
            "config_key": config.config_key,
            "config_value": config.config_value,
            "description": config.description
        })
    except Exception as e:
        return error_response(code=500, message=str(e))

class ConfigManagementCreate(BaseModel):
    config_key: str
    config_value: str
    description: Optional[str] = None

@router.post("", summary="保存或更新配置项")
def save_config(
    config_data: ConfigManagementCreate = Body(...),
    current_user: dict = Depends(get_current_user_or_ak)
):
    db=DB.get_session()
    """保存或更新配置项 (Upsert)"""
    try:
        # 检查config_key是否已存在
        existing_config = db.query(ConfigManagement).filter(ConfigManagement.config_key == config_data.config_key).first()
        
        if existing_config:
            # 更新已有配置
            existing_config.config_value = config_data.config_value
            if config_data.description:
                existing_config.description = config_data.description
            db_config = existing_config
        else:
            # 创建新配置
            db_config = ConfigManagement(
                config_key=config_data.config_key,
                config_value=config_data.config_value,
                description=config_data.description or "AI 配置项"
            )
            db.add(db_config)
            
        db.commit()
        db.refresh(db_config)
        return success_response(data={
            "config_key": db_config.config_key,
            "config_value": db_config.config_value,
            "description": db_config.description
        })
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))

@router.put("/{config_key}", summary="更新配置项")
def update_config(
    config_key: str=Path(...,min_length=1),
    config_data: ConfigManagementCreate = Body(...),
    current_user: dict = Depends(get_current_user_or_ak)
):
    db=DB.get_session()
    """更新配置项"""
    try:
        db_config = db.query(ConfigManagement).filter(ConfigManagement.config_key == config_key).first()
        if not db_config:
            raise HTTPException(status_code=404, detail="Config not found")
        
        if config_data.config_value is not None:
            db_config.config_value = config_data.config_value
        if config_data.description is not None:
            db_config.description = config_data.description
        
        db.commit()
        db.refresh(db_config)
        return success_response(data={
            "config_key": db_config.config_key,
            "config_value": db_config.config_value,
            "description": db_config.description
        })
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))

@router.delete("/{config_key}",summary="删除配置项")
def delete_config(
    config_key: str,
    current_user: dict = Depends(get_current_user_or_ak)
):
    db=DB.get_session()
    """删除配置项"""
    try:
        db_config = db.query(ConfigManagement).filter(ConfigManagement.config_key == config_key).first()
        if not db_config:
            raise HTTPException(status_code=404, detail="Config not found")
        
        db.delete(db_config)
        db.commit()
        return success_response(message="Config deleted successfully")
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))