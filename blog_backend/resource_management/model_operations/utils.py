from abc import ABCMeta, abstractmethod
from typing import Any, Iterable, List, Dict, Any, Generic, TypeVar

from django.db import transaction
from safedelete.models import SafeDeleteModel

from resource_management.models.utils import BaseModel


_T = TypeVar("_T", BaseModel, SafeDeleteModel)


class BaseOperation(Generic[_T], metaclass=ABCMeta):
    @property
    @abstractmethod
    def base_model(self) -> _T:
        pass

    @classmethod
    def create(cls, **kwargs: Any) -> _T:
        return cls.base_model.objects.create(**kwargs)

    @classmethod
    def update(cls, entry: _T, **kwargs: Any) -> _T:
        if not isinstance(entry, cls.base_model):
            raise TypeError("Entry instance does not match with base model.")
        return entry.update(**kwargs)


class BaseBulkOperation(Generic[_T], metaclass=ABCMeta):
    CREATE_BATCH_SIZE = 100
    UPDATE_BATCH_SIZE = 100

    @property
    @abstractmethod
    def base_model(self) -> _T:
        pass

    @classmethod
    def bulk_create(cls, items: Iterable[_T]) -> List[_T]:
        """ Note: Only Postgresql backend will fill PK back to the entries. """
        return cls.base_model.objects.bulk_create(
            items,
            batch_size=cls.CREATE_BATCH_SIZE,
            ignore_conflicts=False,
        )

    @classmethod
    @transaction.atomic
    def bulk_loose_create(cls, items: Iterable[Dict[str, Any]]) -> List[_T]:
        """Note: Django does not support PK filling when 'ignore_conflicts'
        is enabled in bulk_create(). So we need to iterate through the
        dicts and call get_or_create() for entries with PK.
        """
        return [cls.base_model.objects.get_or_create(**item)[0] for item in items]

    @classmethod
    def bulk_update(cls, items: Iterable[_T], fields: Iterable[str]) -> None:
        """ Note: bulk_update does not return entries. """
        cls.base_model.objects.bulk_update(
            items,
            fields,
            batch_size=cls.UPDATE_BATCH_SIZE,
        )
