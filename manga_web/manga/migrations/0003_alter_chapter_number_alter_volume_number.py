# Generated by Django 4.0.5 on 2022-06-07 08:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manga', '0002_volume_converting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chapter',
            name='number',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='volume',
            name='number',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
