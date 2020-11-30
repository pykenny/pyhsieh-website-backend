from django.db import models


class BaseModel(models.Model):
    class Meta:
        abstract = True

    # Expose model manager to object attribute
    objects = models.Manager()
