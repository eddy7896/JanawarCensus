from datetime import datetime
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from ..db.session import Base

@as_declarative()
class BaseModel(Base):
    """Base model that includes common columns and methods"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    @declared_attr
    def __tablename__(cls):
        ""
        Generate table name automatically from class name.
        Converts CamelCase class name to snake_case table name.
        """
        return ''.join(['_' + i.lower() if i.isupper() else i for i in cls.__name__]).lstrip('_')
    
    def to_dict(self):
        ""Convert model instance to dictionary"""
        return {
            column.name: getattr(self, column.name) 
            for column in self.__table__.columns
        }
    
    def update(self, **kwargs):
        ""Update model instance with given attributes"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self
