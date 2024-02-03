# Generated by Django 3.2.23 on 2024-02-03 22:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20240203_2122'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluser',
            name='approver',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='user',
            name='approver',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, to='core.user'),
            preserve_default=False,
        ),
    ]