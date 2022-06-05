# Generated by Django 2.0.4 on 2018-04-08 03:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Manga",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("source", models.URLField(max_length=255)),
                ("total_chap", models.IntegerField(null=True)),
                ("image_src", models.URLField(max_length=255, null=True)),
                ("slug", models.SlugField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Volume",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("chapters", models.IntegerField()),
                ("download_link", models.URLField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "manga",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="manga.Manga"
                    ),
                ),
            ],
        ),
    ]
