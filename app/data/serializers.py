"""
Serializers for data APIs.
"""
from rest_framework import serializers

from core.models import Species, Linelist, SpeciesMetadata, Reference, MetaReference, Line
# from core.models import Reference, Species,
# SpeciesMetadata, MetaReference, Line


class LinelistSerializer(serializers.ModelSerializer):
    """Serialzer for linelists."""
    class Meta:
        model = Linelist
        fields = ['id', 'linelist_name']
        read_only_fields = ['id']


class ReferenceSerializer(serializers.ModelSerializer):
    """Serializer for references."""
    class Meta:
        model = Reference
        fields = ['id', 'doi', 'ref_url', 'bibtex',
                  'entry_date', 'entry_staff', 'notes']
        read_only_fields = ['id', 'entry_date', 'entry_staff', 'bibtex']


class BibFileSerializer(serializers.ModelSerializer):
    """Serializer for uploading .bib files."""
    class Meta:
        model = Reference
        fields = ['id', 'doi', 'ref_url', 'bibtex',
                  'entry_date', 'entry_staff', 'notes']
        read_only_fields = ['id', 'doi', 'ref_url',
                            'entry_date', 'entry_staff', 'notes']


class SpeciesSerializer(serializers.ModelSerializer):
    """Serializer for species."""
    class Meta:
        model = Species
        fields = ['id', 'name', 'iupac_name', 'name_formula', 'name_html',
                  'smiles', 'standard_inchi', 'standard_inchi_key', 'selfies',
                  'entry_date', 'entry_staff', 'notes']
        read_only_fields = ['id', 'selfies', 'entry_date',
                            'entry_staff']


class SpeciesMetadataSerializer(serializers.ModelSerializer):
    """Serializer for species metadata."""
    mu_a = serializers.DecimalField(max_digits=None, decimal_places=None)
    mu_b = serializers.DecimalField(max_digits=None, decimal_places=None)
    mu_c = serializers.DecimalField(max_digits=None, decimal_places=None)
    a_const = serializers.DecimalField(max_digits=None, decimal_places=None)
    b_const = serializers.DecimalField(max_digits=None, decimal_places=None)
    c_const = serializers.DecimalField(max_digits=None, decimal_places=None)

    class Meta:
        model = SpeciesMetadata
        fields = ['id', 'species', 'molecule_tag', 'hyperfine', 'degree_of_freedom',
                  'category', 'partition_function', 'mu_a', 'mu_b', 'mu_c', 'a_const',
                  'b_const', 'c_const', 'linelist', 'data_date', 'data_contributor',
                  'int_file', 'var_file', 'fit_file', 'lin_file', 'entry_date', 'entry_staff', 'notes']
        read_only_fields = ['id', 'int_file', 'var_file',
                            'fit_file', 'lin_file', 'entry_date', 'entry_staff']


class SPFileSerializer(serializers.ModelSerializer):
    """Serializer for uploading SPFIT/SPCAT (.int, .var, .lin, .fit) files.
    This is separate from the SpeciesMetadataSerializer becuase this serializer
    handles specifically upload of SPFIT/SPCAT file types."""
    class Meta:
        model = SpeciesMetadata
        fields = ['id', 'int_file', 'var_file', 'fit_file', 'lin_file']
        read_only_fields = ['id']


class MetaReferenceSerializer(serializers.ModelSerializer):
    """Serializer for metadata references."""
    class Meta:
        model = MetaReference
        fields = ['id', 'meta', 'ref', 'dipole_moment',
                  'spectrum', 'notes', 'entry_date', 'entry_staff']
        read_only_fields = ['id', 'entry_date', 'entry_staff']


class LineSerializer(serializers.ModelSerializer):
    """Serializer for lines."""
    frequency = serializers.DecimalField(max_digits=None, decimal_places=None)
    uncertainty = serializers.DecimalField(
        max_digits=None, decimal_places=None)
    intensity = serializers.DecimalField(max_digits=None, decimal_places=None)
    s_ij = serializers.DecimalField(max_digits=None, decimal_places=None)
    s_ij_mu2 = serializers.DecimalField(max_digits=None, decimal_places=None)
    a_ij = serializers.DecimalField(max_digits=None, decimal_places=None)
    lower_state_energy = serializers.DecimalField(
        max_digits=None, decimal_places=None)
    upper_state_energy = serializers.DecimalField(
        max_digits=None, decimal_places=None)

    class Meta:
        model = Line
        fields = ['id', 'meta', 'measured', 'frequency', 'uncertainty', 'intensity',
                  's_ij', 's_ij_mu2', 'a_ij', 'lower_state_energy', 'upper_state_energy',
                  'upper_state_degeneracy', 'lower_state_qn', 'upper_state_qn', 'rovibrational',
                  'pickett_qn_code', 'pickett_lower_state_qn', 'pickett_upper_state_qn',
                  'entry_date', 'entry_staff', 'notes']
        read_only_fields = ['id', 'entry_date', 'entry_staff']
