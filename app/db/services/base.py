from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseDB(Generic[ModelType]):
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        return self.db.get(self.model, id)

    def get_all(self) -> List[ModelType]:
        return self.db.query(self.model).all()

    def get_by_filter(self, **filters: Any) -> Optional[ModelType]:
        try:
            return self.db.query(self.model).filter_by(**filters).first()
        except NoResultFound:
            return None

    def get_all_by_filter(self, **filters: Any) -> List[ModelType]:
        try:
            return self.db.query(self.model).filter_by(**filters).all()
        except NoResultFound:
            return []

    def create(self, obj_in: Dict[str, Any], commit: bool = True) -> ModelType:
        obj = self.model(**obj_in)
        self.db.add(obj)
        self.db.flush()
        if commit:
            self.db.commit()
            self.db.refresh(obj)
        return obj

    def update(self, _id: Any, obj_in: Dict[str, Any], commit: bool = True) -> Optional[ModelType]:
        db_obj = self.db.get(self.model, _id)
        if db_obj is None:
            return None
        for key, value in obj_in.items():
            setattr(db_obj, key, value)
        if commit:
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete_by_id(self, id: Any) -> Optional[ModelType]:
        obj = self.db.get(self.model, id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj
