# Generated by Django 3.2.22 on 2023-10-31 16:42

import core.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_alter_line_upper_state_energy'),
    ]

    operations = [
        migrations.AddField(
            model_name='species',
            name='molecular_mass',
            field=core.models.ArbitraryDecimalField(null=True),
        ),
    ]
