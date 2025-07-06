from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Tuple
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base class for CRUD operations with default methods to Create, Read, Update, Delete (CRUD)."""

    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict] = None,
        date_filters: Optional[Dict] = None,
        **kwargs
    ) -> Tuple[List[ModelType], int]:
        """Get multiple records with optional filtering and pagination."""
        query = db.query(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        # Apply date range filters
        if date_filters:
            if 'date_from' in date_filters:
                query = query.filter(self.model.created_at >= date_filters['date_from'])
            if 'date_to' in date_filters:
                query = query.filter(self.model.created_at <= date_filters['date_to'])
        
        # Apply additional filters from kwargs
        for key, value in kwargs.items():
            if value is not None and hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return items, total

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, 
        db: Session, 
        *, 
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update a record."""
        obj_data = jsonable_encoder(db_obj)
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data and update_data[field] is not None:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """Delete a record."""
        obj = db.query(self.model).get(id)
        if not obj:
            raise ValueError(f"{self.model.__name__} with id {id} not found")
        db.delete(obj)
        db.commit()
        return obj

    def get_by_field(
        self, 
        db: Session, 
        field: str, 
        value: Any,
        case_insensitive: bool = False
    ) -> Optional[ModelType]:
        """Get a record by a specific field."""
        if not hasattr(self.model, field):
            raise AttributeError(f"{self.model.__name__} has no attribute '{field}'")
        
        query = db.query(self.model)
        
        if case_insensitive and isinstance(value, str):
            query = query.filter(
                getattr(self.model, field).ilike(f"%{value}%")
            )
        else:
            query = query.filter(getattr(self.model, field) == value)
            
        return query.first()

    def get_multi_by_field(
        self, 
        db: Session, 
        field: str, 
        value: Any,
        skip: int = 0, 
        limit: int = 100,
        case_insensitive: bool = False
    ) -> List[ModelType]:
        """Get multiple records by a specific field."""
        if not hasattr(self.model, field):
            raise AttributeError(f"{self.model.__name__} has no attribute '{field}'")
        
        query = db.query(self.model)
        
        if case_insensitive and isinstance(value, str):
            query = query.filter(
                getattr(self.model, field).ilike(f"%{value}%")
            )
        else:
            query = query.filter(getattr(self.model, field) == value)
            
        return query.offset(skip).limit(limit).all()
