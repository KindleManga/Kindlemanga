# Generated by Django 4.0.5 on 2022-06-07 09:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("manga", "0003_alter_chapter_number_alter_volume_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="manga",
            name="thumbnail",
            field=models.ImageField(null=True, upload_to="manga/thumbnail"),
        ),
    ]
