# Generated by Django 3.2.24 on 2024-03-15 04:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_auto_20240315_0414'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicalspeciesmetadata',
            name='contains_rovibrational',
            field=models.BooleanField(),
        ),
        migrations.AlterField(
            model_name='speciesmetadata',
            name='contains_rovibrational',
            field=models.BooleanField(),
        ),
    ]
