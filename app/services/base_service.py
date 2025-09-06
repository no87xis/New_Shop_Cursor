"""
Базовый сервис для всех сервисов
"""
from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel
import logging

from app.models.base import BaseModel as SQLAlchemyBaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=SQLAlchemyBaseModel)
CreateSchema = TypeVar('CreateSchema', bound=BaseModel)
UpdateSchema = TypeVar('UpdateSchema', bound=BaseModel)


class BaseService(Generic[T, CreateSchema, UpdateSchema]):
    """Базовый сервис с CRUD операциями"""
    
    def __init__(self, model: T, db: Session):
        self.model = model
        self.db = db
    
    def create(self, obj_in: CreateSchema) -> T:
        """Создание объекта"""
        try:
            obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"Created {self.model.__name__}: {db_obj.id}")
            return db_obj
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    def get(self, id: int) -> Optional[T]:
        """Получение объекта по ID"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} {id}: {e}")
            return None
    
    def get_multi(self, skip: int = 0, limit: int = 100, filters: Dict[str, Any] = None) -> List[T]:
        """Получение списка объектов"""
        try:
            query = self.db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, key).in_(value))
                        else:
                            query = query.filter(getattr(self.model, key) == value)
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} list: {e}")
            return []
    
    def update(self, id: int, obj_in: UpdateSchema) -> Optional[T]:
        """Обновление объекта"""
        try:
            db_obj = self.get(id)
            if not db_obj:
                return None
            
            obj_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in
            
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"Updated {self.model.__name__}: {id}")
            return db_obj
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model.__name__} {id}: {e}")
            return None
    
    def delete(self, id: int) -> bool:
        """Удаление объекта"""
        try:
            db_obj = self.get(id)
            if not db_obj:
                return False
            
            self.db.delete(db_obj)
            self.db.commit()
            logger.info(f"Deleted {self.model.__name__}: {id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model.__name__} {id}: {e}")
            return False
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """Подсчет количества объектов"""
        try:
            query = self.db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, key).in_(value))
                        else:
                            query = query.filter(getattr(self.model, key) == value)
            
            return query.count()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0
    
    def search(self, search_term: str, search_fields: List[str]) -> List[T]:
        """Поиск объектов по тексту"""
        try:
            query = self.db.query(self.model)
            conditions = []
            
            for field in search_fields:
                if hasattr(self.model, field):
                    conditions.append(
                        getattr(self.model, field).ilike(f"%{search_term}%")
                    )
            
            if conditions:
                query = query.filter(or_(*conditions))
            
            return query.all()
        except Exception as e:
            logger.error(f"Error searching {self.model.__name__}: {e}")
            return []
    
    def exists(self, id: int) -> bool:
        """Проверка существования объекта"""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first() is not None
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__} {id}: {e}")
            return False