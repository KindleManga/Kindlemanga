# Generated by Django 2.0.4 on 2018-10-19 02:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manga', '0006_auto_20180523_0749'),
    ]

    operations = [
        migrations.AddField(
            model_name='volume',
            name='fshare_link',
            field=models.URLField(max_length=500, null=True),
        ),
    ]