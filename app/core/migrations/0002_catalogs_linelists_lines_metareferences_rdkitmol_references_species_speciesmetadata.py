# Generated by Django 3.2.21 on 2023-09-29 17:09

import core.models
from django.conf import settings
import django.contrib.postgres.fields.ranges
from django.db import migrations, models
import django.db.models.deletion
import django_rdkit.models.fields
from django.contrib.postgres.operations import CreateExtension


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        CreateExtension(name='rdkit'),
        migrations.CreateModel(
            name='Catalogs',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('cat_url', models.FileField(upload_to=core.models.cat_file_path)),
                ('entry_date', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
                ('sys_period', django.contrib.postgres.fields.ranges.DateTimeRangeField()),
                ('entry_staff', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Linelists',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('linelist_name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='RDKitMol',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('mol_obj', django_rdkit.models.fields.MolField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Species',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.JSONField()),
                ('iupac_name', models.CharField(max_length=255)),
                ('name_formula', models.CharField(max_length=255)),
                ('name_html', models.CharField(max_length=255)),
                ('canonical_smiles', models.CharField(max_length=255)),
                ('standard_inchi', models.CharField(max_length=255)),
                ('standard_inchi_key', models.CharField(max_length=255)),
                ('entry_date', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
                ('sys_period', django.contrib.postgres.fields.ranges.DateTimeRangeField()),
                ('entry_staff', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('rdkit_mol', models.OneToOneField(
                    on_delete=django.db.models.deletion.PROTECT, to='core.rdkitmol')),
            ],
        ),
        migrations.CreateModel(
            name='SpeciesMetadata',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('molecule_tag', models.IntegerField()),
                ('hyperfine', models.BooleanField()),
                ('degree_of_freedom', models.IntegerField()),
                ('category', models.CharField(max_length=255)),
                ('partition_function', models.JSONField()),
                ('mu_a', models.DecimalField(blank=True,
                 decimal_places=5, max_digits=10, null=True)),
                ('mu_b', models.DecimalField(blank=True,
                 decimal_places=5, max_digits=10, null=True)),
                ('mu_c', models.DecimalField(blank=True,
                 decimal_places=5, max_digits=10, null=True)),
                ('a_const', models.DecimalField(blank=True,
                 decimal_places=4, max_digits=15, null=True)),
                ('b_const', models.DecimalField(blank=True,
                 decimal_places=4, max_digits=15, null=True)),
                ('c_const', models.DecimalField(blank=True,
                 decimal_places=4, max_digits=15, null=True)),
                ('data_date', models.DateField()),
                ('data_contributor', models.CharField(max_length=255)),
                ('entry_date', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
                ('sys_period', django.contrib.postgres.fields.ranges.DateTimeRangeField()),
                ('cat', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to='core.catalogs')),
                ('entry_staff', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('linelist', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to='core.linelists')),
                ('species', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to='core.species')),
            ],
        ),
        migrations.CreateModel(
            name='References',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('doi', models.CharField(blank=True, max_length=255)),
                ('ref_url', models.CharField(max_length=255)),
                ('bibtex', models.TextField()),
                ('entry_date', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
                ('sys_period', django.contrib.postgres.fields.ranges.DateTimeRangeField()),
                ('entry_staff', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MetaReferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('dipole_moment', models.BooleanField()),
                ('spectrum', models.BooleanField()),
                ('notes', models.TextField(blank=True)),
                ('sys_period', django.contrib.postgres.fields.ranges.DateTimeRangeField()),
                ('meta', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to='core.speciesmetadata')),
                ('ref', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to='core.references')),
            ],
        ),
        migrations.CreateModel(
            name='Lines',
            fields=[
                ('id', models.BigAutoField(auto_created=True,
                 primary_key=True, serialize=False, verbose_name='ID')),
                ('measured', models.BooleanField()),
                ('frequency', models.DecimalField(decimal_places=4, max_digits=11)),
                ('uncertainty', models.DecimalField(
                    decimal_places=4, max_digits=11)),
                ('intensity', models.DecimalField(decimal_places=4, max_digits=11)),
                ('s_ij', models.DecimalField(decimal_places=3, max_digits=11)),
                ('s_ij_mu2', models.DecimalField(decimal_places=17, max_digits=25)),
                ('a_ij', models.DecimalField(decimal_places=17, max_digits=25)),
                ('lower_state_energy', models.DecimalField(
                    decimal_places=5, max_digits=20)),
                ('upper_state_energy', models.DecimalField(
                    decimal_places=15, max_digits=25)),
                ('upper_state_degeneracy', models.IntegerField()),
                ('lower_state_qn', models.JSONField()),
                ('upper_state_qn', models.JSONField()),
                ('rovibrational', models.BooleanField()),
                ('pickett_qn_code', models.IntegerField()),
                ('pickett_lower_state_qn', models.JSONField()),
                ('pickett_upper_state_qn', models.JSONField()),
                ('entry_date', models.DateTimeField()),
                ('notes', models.TextField(blank=True)),
                ('sys_period', django.contrib.postgres.fields.ranges.DateTimeRangeField()),
                ('entry_staff', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('meta', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT, to='core.speciesmetadata')),
            ],
        ),
    ]
