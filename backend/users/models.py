from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email_verified = models.BooleanField(default=False)
    email = models.EmailField(unique=True)

    def save(self, *args, **kwargs):
        self.username = self.username.lower()
        super(CustomUser, self).save(*args, **kwargs)
