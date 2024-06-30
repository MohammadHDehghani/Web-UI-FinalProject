from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Object(models.Model):
    name = models.CharField(max_length=255)
    size = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, related_name='owned_objects', on_delete=models.CASCADE)
    users_with_access = models.ManyToManyField(User, related_name='accessible_objects')
    extension = models.CharField(max_length=10)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'owner'], name='unique_name_per_owner')
        ]

    def __str__(self):
        return self.name
