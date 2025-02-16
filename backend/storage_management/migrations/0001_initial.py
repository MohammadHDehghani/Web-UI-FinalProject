# Generated by Django 5.0.6 on 2024-06-30 14:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Object',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('size', models.PositiveIntegerField()),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_objects', to=settings.AUTH_USER_MODEL)),
                ('users_with_access', models.ManyToManyField(related_name='accessible_objects', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
