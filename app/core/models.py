"""
Database models.
"""
import uuid
import os
from django.conf import settings
from django_rdkit import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.contrib.postgres.fields import DateTimeRangeField


def cat_file_path(instance, filename):
    """Generate file path for cat file."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'
    return os.path.join('uploads', 'cat', filename)


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(self, email, password, name, organization):
        """Create, save and return a new user."""
        if not email or not password or not name or not organization:
            raise ValueError('User must have an email, \
                              password, name, and organization')
        user = self.model(email=self.normalize_email(email),
                          name=name, organization=organization)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password, name, organization):
        """Create and return a new superuser."""
        user = self.create_user(email, password, name, organization)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Users in the system."""
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    organization = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=True)

    REQUIRED_FIELDS = ['name', 'organization']
    objects = UserManager()

    USERNAME_FIELD = 'email'


class RdkitMol(models.Model):
    mol_obj = models.MolField(blank=True, null=True)


class Linelists(models.Model):
    linelist_name = models.CharField(max_length=255)


class Catalogs(models.Model):
    """Catalogs object."""
    cat_url = models.FileField(upload_to=cat_file_path)
    entry_date = models.DateTimeField()
    entry_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    notes = models.TextField(blank=True)
    sys_period = DateTimeRangeField()


class References(models.Model):
    """References object."""
    doi = models.CharField(max_length=255, blank=True)
    ref_url = models.CharField(max_length=255)
    bibtex = models.TextField()
    entry_date = models.DateTimeField()
    entry_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    notes = models.TextField(blank=True)
    sys_period = DateTimeRangeField()


class Species(models.Model):
    name = models.JSONField()
    iupac_name = models.CharField(max_length=255)
    name_formula = models.CharField(max_length=255)
    name_html = models.CharField(max_length=255)
    canonical_smiles = models.CharField(max_length=255)
    standard_inchi = models.CharField(max_length=255)
    standard_inchi_key = models.CharField(max_length=255)
    rdkit_mol = models.OneToOneField(
        'RdkitMol',
        on_delete=models.PROTECT)
    entry_date = models.DateTimeField()
    entry_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    notes = models.TextField(blank=True)
    sys_period = DateTimeRangeField()


class SpeciesMetadata(models.Model):
    species = models.ForeignKey(
        'Species',
        on_delete=models.PROTECT
    )
    molecule_tag = models.IntegerField()
    hyperfine = models.BooleanField()
    degree_of_freedom = models.IntegerField()
    category = models.CharField(max_length=255)
    partition_function = models.JSONField()
    mu_a = models.DecimalField(
        max_digits=10, decimal_places=5, blank=True, null=True)
    mu_b = models.DecimalField(
        max_digits=10, decimal_places=5, blank=True, null=True)
    mu_c = models.DecimalField(
        max_digits=10, decimal_places=5, blank=True, null=True)
    a_const = models.DecimalField(
        max_digits=15, decimal_places=4, blank=True, null=True)
    b_const = models.DecimalField(
        max_digits=15, decimal_places=4, blank=True, null=True)
    c_const = models.DecimalField(
        max_digits=15, decimal_places=4, blank=True, null=True)
    cat = models.ForeignKey(
        'Catalogs',
        on_delete=models.PROTECT
    )
    linelist = models.ForeignKey(
        'Linelists',
        on_delete=models.PROTECT
    )
    data_date = models.DateField()
    data_contributor = models.CharField(max_length=255)
    entry_date = models.DateTimeField()
    entry_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    notes = models.TextField(blank=True)
    sys_period = DateTimeRangeField()


class MetaReferences(models.Model):
    """Metadata references object."""
    meta = models.ForeignKey(
        'SpeciesMetadata',
        on_delete=models.PROTECT
    )
    ref = models.ForeignKey(
        'References',
        on_delete=models.PROTECT
    )
    dipole_moment = models.BooleanField()
    spectrum = models.BooleanField()
    notes = models.TextField(blank=True)
    sys_period = DateTimeRangeField()


class Lines(models.Model):
    """Lines object."""
    meta = models.ForeignKey(
        'SpeciesMetadata',
        on_delete=models.PROTECT
    )
    measured = models.BooleanField()
    frequency = models.DecimalField(max_digits=11, decimal_places=4)
    uncertainty = models.DecimalField(max_digits=11, decimal_places=4)
    intensity = models.DecimalField(max_digits=11, decimal_places=4)
    s_ij = models.DecimalField(max_digits=11, decimal_places=3)
    s_ij_mu2 = models.DecimalField(max_digits=25, decimal_places=17)
    a_ij = models.DecimalField(max_digits=25, decimal_places=17)
    lower_state_energy = models.DecimalField(max_digits=20, decimal_places=5)
    upper_state_energy = models.DecimalField(max_digits=25, decimal_places=15)
    upper_state_degeneracy = models.IntegerField()
    lower_state_qn = models.JSONField()
    upper_state_qn = models.JSONField()
    rovibrational = models.BooleanField()
    pickett_qn_code = models.IntegerField()
    pickett_lower_state_qn = models.JSONField()
    pickett_upper_state_qn = models.JSONField()
    entry_date = models.DateTimeField()
    entry_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    notes = models.TextField(blank=True)
    sys_period = DateTimeRangeField()
