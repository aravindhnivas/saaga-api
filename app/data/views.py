"""
Views for data APIs.
"""
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Species
from data import serializers
from rdkit import Chem
import json


class SpeciesViewSet(viewsets.ModelViewSet):
    """View for get and create species APIs."""
    serializer_class = serializers.SpeciesSerializer
    queryset = Species.objects.all()
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve species """
        return self.queryset.order_by('-id')

    def perform_create(self, serializer):
        """Create a new species."""
        received_json = json.dumps(self.request.data)
        json_dict = json.loads(received_json)
        smiles = json_dict['canonical_smiles']
        rdkit_mol_obj = Chem.MolFromSmiles(smiles)
        serializer.save(entry_staff=self.request.user, mol_obj=rdkit_mol_obj)
