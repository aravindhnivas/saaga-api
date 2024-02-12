# Generated by Django 3.2.23 on 2024-02-12 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_auto_20240208_1952'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='historicalspeciesmetadata',
            options={'get_latest_by': ('history_date', 'history_id'), 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical species metadata', 'verbose_name_plural': 'historical species metadatas'},
        ),
        migrations.AlterModelOptions(
            name='speciesmetadata',
            options={},
        ),
        migrations.RemoveIndex(
            model_name='line',
            name='core_line_frequen_cc6179_idx',
        ),
        migrations.AlterField(
            model_name='historicallinelist',
            name='approved',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='historicalmetareference',
            name='approved',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='historicalreference',
            name='approved',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='historicalreference',
            name='doi',
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='historicalspecies',
            name='approved',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='historicalspeciesmetadata',
            name='approved',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='historicalspeciesmetadata',
            name='hyperfine',
            field=models.BooleanField(db_index=True),
        ),
        migrations.AlterField(
            model_name='historicalspeciesmetadata',
            name='molecule_tag',
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='linelist',
            name='approved',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='linelist',
            name='linelist_name',
            field=models.CharField(db_index=True, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='metareference',
            name='approved',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='reference',
            name='approved',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='reference',
            name='doi',
            field=models.CharField(blank=True, db_index=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='species',
            name='approved',
            field=models.BooleanField(db_index=True, default=True),
        ),
        migrations.AlterField(
            model_name='species',
            name='iupac_name',
            field=models.CharField(db_index=True, max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='speciesmetadata',
            name='approved',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='speciesmetadata',
            name='hyperfine',
            field=models.BooleanField(db_index=True),
        ),
        migrations.AlterField(
            model_name='speciesmetadata',
            name='molecule_tag',
            field=models.IntegerField(blank=True, db_index=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='metareference',
            unique_together={('meta', 'ref', 'dipole_moment', 'spectrum')},
        ),
        migrations.AlterUniqueTogether(
            name='speciesmetadata',
            unique_together={('species', 'linelist', 'molecule_tag', 'hyperfine')},
        ),
        migrations.AddIndex(
            model_name='line',
            index=models.Index(fields=['frequency', 'meta'], name='core_line_frequen_8bf172_idx'),
        ),
    ]
