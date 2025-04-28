"""
Serializers for data APIs.
"""

from rest_framework import serializers

from core.models import (
    Species,
    Linelist,
    SpeciesMetadata,
    SpeciesMetadataMiscFileUpload,
    Reference,
    MetaReference,
    Line,
    BaseModel
)
from rdkit import Chem
from rdkit.Chem import AllChem
# --- Base Serializers ---

class BaseSerializer(serializers.ModelSerializer):
    """
    Base serializer for models inheriting from BaseModel.
    Includes common status and tracking fields.
    """
    status = serializers.ChoiceField(choices=BaseModel.STATUS_CHOICES, required=False)
    uploaded_by_name = serializers.CharField(source='uploaded_by.name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.name', read_only=True, allow_null=True)

    class Meta:
        # No model defined here, subclasses will specify it
        fields = [
            "id",
            "status",
            "uploaded_by",
            "uploaded_by_name",
            "processed_by",
            "processed_by_name",
            "processed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "uploaded_by",
            "uploaded_by_name",
            "processed_by",
            "processed_by_name",
            "processed_at",
            "created_at",
        ]

# Change inheritance from serializers.ModelSerializer to BaseSerializer
class LinelistSerializer(BaseSerializer):
    """Serializer for linelists."""

    class Meta(BaseSerializer.Meta): # Inherit Meta from BaseSerializer
        model = Linelist
        # Add model-specific fields to the base fields
        fields = BaseSerializer.Meta.fields + ["linelist_name"]
        # Inherit read_only_fields from BaseSerializer
        # read_only_fields are inherited, no need to redefine unless adding more
        

# Change inheritance to LinelistSerializer
class LinelistChangeSerializer(LinelistSerializer):
    """Serializer for put and patch linelists."""
    # Add change reason directly
    _change_reason = serializers.CharField(
        max_length=255, write_only=True, required=True
    )

    class Meta(LinelistSerializer.Meta): # Inherit Meta from LinelistSerializer
        # Add _change_reason to the fields inherited from LinelistSerializer
        fields = LinelistSerializer.Meta.fields + ["_change_reason"]
        # Define read_only_fields specifically for the update context.
        # Usually, only system/base fields that should never change are read-only here.
        # Fields like 'linelist_name' should NOT be read-only during an update.
        read_only_fields = BaseSerializer.Meta.read_only_fields # Start with base system read-only fields
        
# Change inheritance from serializers.ModelSerializer to BaseSerializer
class ReferenceSerializer(BaseSerializer):
    """Serializer for references."""

    class Meta(BaseSerializer.Meta): # Inherit Meta from BaseSerializer
        model = Reference
        # Update fields list: remove approved/rejected, base fields are inherited
        fields = BaseSerializer.Meta.fields + [
            "doi",
            "ref_url",
            "bibtex",
            "notes",
        ]

# Change inheritance to ReferenceSerializer
class ReferenceChangeSerializer(ReferenceSerializer):
    """Serializer for put and patch references."""
    # Add change reason directly
    _change_reason = serializers.CharField(
        max_length=255, write_only=True, required=True
    )
    # Override bibtex if it needs to be writable here but was read-only in ReferenceSerializer
    bibtex = serializers.FileField(required=False, allow_null=True)

    class Meta(ReferenceSerializer.Meta): # Inherit Meta from ReferenceSerializer
        # Add _change_reason to the fields inherited from ReferenceSerializer
        fields = ReferenceSerializer.Meta.fields + ["_change_reason"]
        # Define read_only_fields for the update context.
        # Fields like 'doi', 'ref_url', 'notes', 'bibtex' should NOT be read-only here.
        read_only_fields = BaseSerializer.Meta.read_only_fields # Start with base system read-only fields


def smiles_to_pdb_string(smiles_string):
    try:
        mol = Chem.MolFromSmiles(smiles_string)
        if mol is None:
            return None, "Invalid SMILES string"
        mol_with_h = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol_with_h, AllChem.ETKDGv3())
        AllChem.MMFFOptimizeMolecule(mol_with_h)
        pdb_string = Chem.MolToPDBBlock(mol_with_h)
        return pdb_string, None
    except Exception as e:
        return None, str(e)
    
# Change inheritance from serializers.ModelSerializer to BaseSerializer
class SpeciesSerializer(BaseSerializer):
    """Serializer for species."""

    molecular_mass = serializers.DecimalField(
        max_digits=None, decimal_places=None, read_only=True
    )
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["pdb_data"] = smiles_to_pdb_string(instance.smiles)
        return representation

    class Meta(BaseSerializer.Meta): # Inherit Meta from BaseSerializer
        model = Species
        # Update fields list: remove approved/rejected, base fields are inherited
        fields = BaseSerializer.Meta.fields + [
            "name",
            "iupac_name",
            "name_formula",
            "name_html",
            "molecular_mass",
            "smiles",
            "standard_inchi",
            "standard_inchi_key",
            "selfies",
            "notes",
        ]
        # Update read_only_fields: base fields are inherited, add specifics
        read_only_fields = BaseSerializer.Meta.read_only_fields + [
            "molecular_mass",
            "selfies",
        ]

# Change inheritance to SpeciesSerializer
class SpeciesChangeSerializer(SpeciesSerializer):
    """Serializer for put and patch species."""
    # Add change reason directly
    _change_reason = serializers.CharField(
        max_length=255, write_only=True, required=True
    )
    # Define mol_obj here if it's only relevant for updates
    mol_obj = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta(SpeciesSerializer.Meta): # Inherit Meta from SpeciesSerializer
        # Add _change_reason and potentially mol_obj to inherited fields
        # Ensure mol_obj isn't duplicated if already added in SpeciesSerializer
        _extra_fields = ["_change_reason"]
        if "mol_obj" not in SpeciesSerializer.Meta.fields:
             _extra_fields.append("mol_obj")
        fields = SpeciesSerializer.Meta.fields + _extra_fields

        # Define read_only_fields for the update context.
        # Inherited fields like 'molecular_mass', 'selfies' remain read-only.
        # Fields like 'name', 'smiles', 'notes', 'mol_obj' should NOT be read-only here.
        read_only_fields = BaseSerializer.Meta.read_only_fields + [
            "molecular_mass", # Calculated field
            "selfies",        # Derived field
        ]

# Change inheritance from serializers.ModelSerializer to BaseSerializer
class SpeciesMetadataSerializer(BaseSerializer):
    """Serializer for species metadata."""

    # Keep DecimalField definitions
    mu_a = serializers.DecimalField(max_digits=None, decimal_places=None, required=False, allow_null=True)
    mu_b = serializers.DecimalField(max_digits=None, decimal_places=None, required=False, allow_null=True)
    mu_c = serializers.DecimalField(max_digits=None, decimal_places=None, required=False, allow_null=True)
    a_const = serializers.DecimalField(max_digits=None, decimal_places=None, required=False, allow_null=True)
    b_const = serializers.DecimalField(max_digits=None, decimal_places=None, required=False, allow_null=True)
    c_const = serializers.DecimalField(max_digits=None, decimal_places=None, required=False, allow_null=True)

    # Add related object names for readability using source=
    species_smiles = serializers.CharField(source='species.smiles', read_only=True)
    species_formula = serializers.CharField(source='species.name_formula', read_only=True)
    species_name = serializers.CharField(source='species.iupac_name', read_only=True)
    linelist_name = serializers.CharField(source='linelist.linelist_name', read_only=True)

    class Meta(BaseSerializer.Meta): # Inherit Meta from BaseSerializer
        model = SpeciesMetadata
        # Update fields list: remove approved/rejected, base fields are inherited, add source fields
        fields = BaseSerializer.Meta.fields + [
            "species", # ID for relation
            "species_smiles", # Read-only representation field
            "species_formula",# Read-only representation field
            "species_name",   # Read-only representation field
            "molecule_tag",
            "hyperfine",
            "degree_of_freedom",
            "category",
            "partition_function",
            "mu_a",
            "mu_b",
            "mu_c",
            "a_const",
            "b_const",
            "c_const",
            "linelist", # ID for relation
            "linelist_name", # Read-only representation field
            "data_date",
            "data_contributor",
            "qpart_file",
            "int_file",
            "var_file",
            "fit_file",
            "lin_file",
            "cat_file",
            "vib_qn",
            "contains_rovibrational",
            "qn_label_str",
            "notes",
            "cat_file_added",
            "request_immediate_approval",
        ]
        # Update read_only_fields: base fields inherited, add specifics and source fields
        read_only_fields = BaseSerializer.Meta.read_only_fields + [
            "partition_function",
            "cat_file",
            "vib_qn",
            "contains_rovibrational",
            "qn_label_str",
            "cat_file_added",
            "species_smiles",
            "species_formula",
            "species_name",
            "linelist_name",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Dynamically add misc files list
        representation["misc_files"] = [
            {"url": file.misc_file.url.replace("/static/media", ""), "name": file.name}
            for file in instance.misc_files.filter(status=BaseModel.STATUS_APPROVED) # Example filter
        ]
        return representation

# Change inheritance to SpeciesMetadataSerializer
class SpeciesMetadataChangeSerializer(SpeciesMetadataSerializer):
    """Serializer for put and patch species metadata."""
    # Add change reason directly
    _change_reason = serializers.CharField(
        max_length=255, write_only=True, required=True
    )
    # Override file fields to make them writable if they weren't in the base
    qpart_file = serializers.FileField(required=False, allow_null=True)
    int_file = serializers.FileField(required=False, allow_null=True)
    var_file = serializers.FileField(required=False, allow_null=True)
    fit_file = serializers.FileField(required=False, allow_null=True)
    lin_file = serializers.FileField(required=False, allow_null=True)

    # Decimal fields definitions are inherited if not overridden

    class Meta(SpeciesMetadataSerializer.Meta): # Inherit Meta from SpeciesMetadataSerializer
        # Add _change_reason to the fields inherited from SpeciesMetadataSerializer
        fields = SpeciesMetadataSerializer.Meta.fields + ["_change_reason"]

        # Define read_only_fields for the update context.
        # Keep the generated/derived fields read-only.
        # Fields like 'species', 'linelist', 'notes', 'mu_a', file fields etc. should NOT be read-only here.
        # The source-based fields (species_name etc.) are inherently read-only from the parent.
        read_only_fields = BaseSerializer.Meta.read_only_fields + [
            # Fields from parent that remain read-only during update
            "partition_function",
            "cat_file",
            "vib_qn",
            "contains_rovibrational",
            "qn_label_str",
            "cat_file_added",
            # Representation fields are inherently read-only via source=
            "species_smiles",
            "species_formula",
            "species_name",
            "linelist_name",
        ]

# Change inheritance from serializers.ModelSerializer to BaseSerializer
class SpeciesMetadataMiscFileUploadSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta): # Inherit Meta from BaseSerializer
        model = SpeciesMetadataMiscFileUpload
        # Update fields list: remove approved/rejected, base fields are inherited
        fields = BaseSerializer.Meta.fields + [
            "meta",
            "misc_file",
            "name",
            "notes",
        ]
        # read_only_fields inherited

# Change inheritance from serializers.ModelSerializer to BaseSerializer
class MetaReferenceSerializer(BaseSerializer):
    """Serializer for metadata references."""
    # Add related names using source=
    species_formula = serializers.CharField(source='meta.species.name_formula', read_only=True)
    species_name = serializers.CharField(source='meta.species.iupac_name', read_only=True)
    molecule_tag = serializers.IntegerField(source='meta.molecule_tag', read_only=True)
    linelist_name = serializers.CharField(source='meta.linelist.linelist_name', read_only=True)
    doi = serializers.CharField(source='ref.doi', read_only=True)
    ref_url = serializers.CharField(source='ref.ref_url', read_only=True)

    class Meta(BaseSerializer.Meta): # Inherit Meta from BaseSerializer
        model = MetaReference
        # Update fields list: remove approved/rejected, base fields inherited, add source fields
        fields = BaseSerializer.Meta.fields + [
            "meta", # Relation ID
            "ref",  # Relation ID
            "species_formula", # Read-only representation
            "species_name",    # Read-only representation
            "molecule_tag",    # Read-only representation
            "linelist_name",   # Read-only representation
            "doi",             # Read-only representation
            "ref_url",         # Read-only representation
            "dipole_moment",
            "spectrum",
            "notes",
        ]
        # Update read_only_fields: base fields inherited, add source fields
        read_only_fields = BaseSerializer.Meta.read_only_fields + [
            "species_formula",
            "species_name",
            "molecule_tag",
            "linelist_name",
            "doi",
            "ref_url",
        ]

# Change inheritance to MetaReferenceSerializer
class MetaReferenceChangeSerializer(MetaReferenceSerializer):
    """Serializer for put and patch metadata references."""
    # Add change reason directly
    _change_reason = serializers.CharField(
        max_length=255, write_only=True, required=True
    )

    class Meta(MetaReferenceSerializer.Meta): # Inherit Meta from MetaReferenceSerializer
        # Add _change_reason to the fields inherited from MetaReferenceSerializer
        fields = MetaReferenceSerializer.Meta.fields + ["_change_reason"]
        # Define read_only_fields for the update context.
        # Representation fields (species_name etc.) are inherently read-only from parent.
        # Fields like 'meta', 'ref', 'notes', 'dipole_moment', 'spectrum' should NOT be read-only here.
        read_only_fields = BaseSerializer.Meta.read_only_fields + [
             # Representation fields are inherently read-only via source=
            "species_formula",
            "species_name",
            "molecule_tag",
            "linelist_name",
            "doi",
            "ref_url",
        ]
class LineSerializer(serializers.ModelSerializer):
    qn_label_str = serializers.CharField()
    vib_qn = serializers.CharField(required=False, allow_blank=True)
    contains_rovibrational = serializers.BooleanField()
    notes = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Line
        fields = [
            "meta",
            "qn_label_str",
            "vib_qn",
            "contains_rovibrational",
            "notes",
        ]


class LineSerializerList(serializers.ModelSerializer):
    """Serializer for creating lines in the backend
    after receiving POST request."""

    frequency = serializers.DecimalField(max_digits=None, decimal_places=None)
    uncertainty = serializers.DecimalField(max_digits=None, decimal_places=None)
    intensity = serializers.DecimalField(max_digits=None, decimal_places=None)
    s_ij = serializers.DecimalField(
        max_digits=None, decimal_places=None, required=False, allow_null=True
    )
    s_ij_mu2 = serializers.DecimalField(max_digits=None, decimal_places=None)
    a_ij = serializers.DecimalField(max_digits=None, decimal_places=None)
    lower_state_energy = serializers.DecimalField(max_digits=None, decimal_places=None)
    upper_state_energy = serializers.DecimalField(max_digits=None, decimal_places=None)

    class Meta:
        model = Line
        # Remove commented-out status fields
        fields = [
            "id",
            "meta",
            "measured",
            "frequency",
            "uncertainty",
            "intensity",
            "s_ij",
            "s_ij_mu2",
            "a_ij",
            "upper_state_energy",
            "lower_state_energy",
            "upper_state_degeneracy",
            "lower_state_degeneracy",
            "upper_state_qn",
            "lower_state_qn",
            "rovibrational",
            "vib_qn",
            "pickett_qn_code",
            "pickett_upper_state_qn",
            "pickett_lower_state_qn",
            "notes",
            # REMOVED: "uploaded_by",
            # REMOVED: "approved",
            # REMOVED: "created_at",
        ]
        # Remove commented-out status fields from read_only
        read_only_fields = [
            "id",
            # REMOVED: "uploaded_by", "created_at"
        ]


# Change inheritance to LineSerializerList
# NOTE: Assumes LineSerializerList is the primary serializer for create/update operations for Lines
class LineChangeSerializerList(LineSerializerList):
    """Serializer for put and patch lines."""
    # Add change reason directly
    _change_reason = serializers.CharField(
        max_length=255, write_only=True, required=True
    )

    class Meta(LineSerializerList.Meta): # Inherit Meta from LineSerializerList
        # Add _change_reason to the fields inherited from LineSerializerList
        fields = LineSerializerList.Meta.fields + ["_change_reason"]
        # Define read_only_fields for update context. Usually just 'id'.
        read_only_fields = ["id"]

class QuerySerializer(serializers.ModelSerializer):
    """Serilizer for querying lines falling
    within specified frequency range."""

    frequency = serializers.DecimalField(max_digits=None, decimal_places=None)
    uncertainty = serializers.DecimalField(max_digits=None, decimal_places=None)
    intensity = serializers.DecimalField(max_digits=None, decimal_places=None)
    s_ij = serializers.DecimalField(max_digits=None, decimal_places=None)
    s_ij_mu2 = serializers.DecimalField(max_digits=None, decimal_places=None)
    a_ij = serializers.DecimalField(max_digits=None, decimal_places=None)
    lower_state_energy = serializers.DecimalField(max_digits=None, decimal_places=None)
    upper_state_energy = serializers.DecimalField(max_digits=None, decimal_places=None)
    
    
    name_formula = serializers.CharField(source='meta.species.name_formula', read_only=True)
    iupac_name = serializers.CharField(source='meta.species.iupac_name', read_only=True)
    name = serializers.JSONField(source='meta.species.name', read_only=True)
    molecule_tag = serializers.IntegerField(source='meta.molecule_tag', read_only=True)
    hyperfine = serializers.BooleanField(source='meta.hyperfine', read_only=True)
    linelist = serializers.CharField(source='meta.linelist.linelist_name', read_only=True)
    meta_id = serializers.IntegerField(source='meta.id', read_only=True)
    smiles = serializers.CharField(source='meta.species.smiles', read_only=True)
    selfies = serializers.CharField(source='meta.species.selfies', read_only=True)
    
    class Meta:
        model = Line
        # Remove commented-out status fields
        fields = [
            "id", # Add Line ID
            "frequency",
            "measured",
            "uncertainty",
            "intensity",
            "lower_state_qn",
            "upper_state_qn",
            "lower_state_energy",
            "upper_state_energy",
            "s_ij",
            "s_ij_mu2",
            "a_ij",
            "rovibrational",
            "name_formula",
            "iupac_name",
            "name",
            "molecule_tag",
            "hyperfine",
            "linelist",
            "meta_id",
            "smiles",
            "selfies",
        ]
        read_only_fields = fields # All fields are read-only