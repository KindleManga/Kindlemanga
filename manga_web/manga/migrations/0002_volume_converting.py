# Generated by Django 4.0.5 on 2022-06-07 05:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manga', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='volume',
            name='converting',
            field=models.BooleanField(default=False),
        ),
    ]