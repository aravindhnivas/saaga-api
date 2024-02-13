# Generated by Django 3.2.23 on 2024-02-13 22:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20240212_1844'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicallinelist',
            name='approved',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='historicalspecies',
            name='name_formula',
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='linelist',
            name='approved',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='species',
            name='name_formula',
            field=models.CharField(db_index=True, max_length=255),
        ),
    ]
