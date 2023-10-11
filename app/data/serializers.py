"""
Serializers for data APIs.
"""
from rest_framework import serializers

from core.models import Species, Linelist, SpeciesMetadata
# from core.models import Reference, Species,
# SpeciesMetadata, MetaReference, Line


class SpeciesSerializer(serializers.ModelSerializer):
    """Serializer for species."""
    class Meta:
        model = Species
        fields = ['id', 'name', 'iupac_name', 'name_formula', 'name_html',
                  'smiles', 'standard_inchi', 'standard_inchi_key',
                  'entry_date', 'entry_staff', 'notes']
        read_only_fields = ['id', 'entry_date',
                            'entry_staff']


class LinelistSerializer(serializers.ModelSerializer):
    """Serialzer for linelists."""
    class Meta:
        model = Linelist
        fields = ['id', 'linelist_name']
        read_only_fields = ['id']


class SpeciesMetadataSerializer(serializers.ModelSerializer):
    """Serializer for species metadata."""
    class Meta:
        model = SpeciesMetadata
        fields = ['id', 'species', 'molecule_tag', 'hyperfine', 'degree_of_freedom',
                  'category', 'partition_function', 'mu_a', 'mu_b', 'mu_c', 'a_const',
                  'b_const', 'c_const', 'linelist', 'data_date', 'data_contributor',
                  'int_file', 'var_file', 'fit_file', 'lin_file', 'entry_date', 'entry_staff', 'notes']
        read_only_fields = ['id', 'entry_date', 'entry_staff']


class SPFileSerializer(serializers.ModelSerializer):
    """Serializer for uploading SPFIT/SPCAT (.int, .var, .lin, .fit) files.
    This is separate from the SpeciesMetadataSerializer becuase this serializer
    handles specifically upload of SPFIT/SPCAT file types."""
    class Meta:
        model = SpeciesMetadata
        fields = ['id', 'int_file', 'var_file', 'fit_file', 'lin_file']
        read_only_fields = ['id']
