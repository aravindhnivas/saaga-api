"""
Serializers for data APIs.
"""
from rest_framework import serializers

from core.models import Species
# from core.models import Linelist, Catalog, Reference, Species,
# SpeciesMetadata, MetaReference, Line


class SpeciesSerializer(serializers.ModelSerializer):
    """Serializer for species."""
    class Meta:
        model = Species
        fields = ['id', 'name', 'iupac_name', 'name_formula', 'name_html',
                  'canonical_smiles', 'standard_inchi', 'standard_inchi_key',
                  'entry_date', 'entry_staff', 'notes']
        read_only_fields = ['id', 'entry_date',
                            'entry_staff']
