"""
Database models.
"""
import os
import uuid
from django.conf import settings
from django_rdkit import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin
)
from django.utils.functional import cached_property
from django.utils.html import format_html
from rdkit.Chem import Draw
import base64
from django.core.validators import FileExtensionValidator


def sp_file_path(instance, filename):
    """Generate file path for SPFIT/SPCAT (.int, .var, .lin, .fit) files."""
    ext = os.path.splitext(filename)[1]
    filename = f'{uuid.uuid4()}{ext}'
    return os.path.join('uploads', 'data', filename)


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


class Linelist(models.Model):
    linelist_name = models.CharField(max_length=255, unique=True)

    def save(self, *args, **kwargs):
        self.linelist_name = self.linelist_name.lower()
        return super(Linelist, self).save(*args, **kwargs)


class Reference(models.Model):
    """References object."""
    doi = models.CharField(max_length=255, blank=True)
    ref_url = models.CharField(max_length=255)
    bibtex = models.TextField()
    entry_date = models.DateTimeField(auto_now_add=True)
    entry_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    notes = models.TextField(blank=True)


class Species(models.Model):
    class Meta:
        verbose_name_plural = 'Species'
    name = models.JSONField()
    iupac_name = models.CharField(max_length=255, unique=True)
    name_formula = models.CharField(max_length=255)
    name_html = models.CharField(max_length=255)
    smiles = models.CharField(max_length=255, unique=True)
    standard_inchi = models.CharField(max_length=255, unique=True)
    standard_inchi_key = models.CharField(max_length=255, unique=True)
    mol_obj = models.MolField(blank=True, null=True)
    entry_date = models.DateTimeField(auto_now_add=True)
    entry_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    notes = models.TextField(blank=True)

    @cached_property
    def display_mol(self):
        if self.mol_obj:
            dm = Draw.PrepareMolForDrawing(self.mol_obj)
            d2d = Draw.MolDraw2DCairo(400, 400)
            d2d.DrawMolecule(dm)
            d2d.FinishDrawing()
            text = d2d.GetDrawingText()
            imtext = base64.b64encode(text).decode('utf8')
            html = '<img src="data:image/png;base64, {img}" alt="rdkit image">'
            return format_html(html, img=imtext)
        return format_html('<strong>There is no image for this entry.<strong>')
    display_mol.short_description = 'Display rdkit image'


class SpeciesMetadata(models.Model):
    class Meta:
        verbose_name_plural = 'Species metadata'
    species = models.ForeignKey(
        'Species',
        on_delete=models.PROTECT
    )
    molecule_tag = models.IntegerField(blank=True)
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
    linelist = models.ForeignKey(
        'Linelist',
        on_delete=models.PROTECT
    )
    data_date = models.DateField()
    data_contributor = models.CharField(max_length=255)
    int_file = models.FileField(null=True, upload_to=sp_file_path,
                                validators=[FileExtensionValidator(
                                    allowed_extensions=["int"])])
    var_file = models.FileField(null=True, upload_to=sp_file_path,
                                validators=[FileExtensionValidator(
                                    allowed_extensions=["var"])])
    fit_file = models.FileField(null=True, upload_to=sp_file_path,
                                validators=[FileExtensionValidator(
                                    allowed_extensions=["fit"])])
    lin_file = models.FileField(null=True, upload_to=sp_file_path,
                                validators=[FileExtensionValidator(
                                    allowed_extensions=["lin"])])
    entry_date = models.DateTimeField(auto_now_add=True)
    entry_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    notes = models.TextField(blank=True)


class MetaReference(models.Model):
    """Metadata references object."""
    meta = models.ForeignKey(
        'SpeciesMetadata',
        on_delete=models.PROTECT
    )
    ref = models.ForeignKey(
        'Reference',
        on_delete=models.PROTECT
    )
    dipole_moment = models.BooleanField()
    spectrum = models.BooleanField()
    notes = models.TextField(blank=True)


class Line(models.Model):
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
    entry_date = models.DateTimeField(auto_now_add=True)
    entry_staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT
    )
    notes = models.TextField(blank=True)
