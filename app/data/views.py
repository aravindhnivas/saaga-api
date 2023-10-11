"""
Views for data APIs.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Species, Linelist, SpeciesMetadata
from data import serializers
from rdkit import Chem
import json


class SpeciesViewSet(viewsets.ModelViewSet):
    """View for species APIs."""
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
        smiles = json_dict['smiles']
        canonical_smiles = Chem.CanonSmiles(smiles)
        rdkit_mol_obj = Chem.MolFromSmiles(canonical_smiles)
        serializer.save(entry_staff=self.request.user, mol_obj=rdkit_mol_obj,
                        smiles=canonical_smiles)


class LinelistViewSet(viewsets.ModelViewSet):
    """View for linelist APIs."""
    serializer_class = serializers.LinelistSerializer
    queryset = Linelist.objects.all()
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve linelists."""
        return self.queryset.order_by('-id')


class SpeciesMetadataViewSet(viewsets.ModelViewSet):
    """View for species metadata APIs."""
    serializer_class = serializers.SpeciesMetadataSerializer
    queryset = SpeciesMetadata.objects.all()
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve species metadata."""
        return self.queryset.order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'upload_file':
            return serializers.SPFileSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new species metadata."""
        serializer.save(entry_staff=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-file')
    def upload_file(self, request, pk=None):
        """Upload a file to species metadata."""
        species_metadata = self.get_object()
        serializer = self.get_serializer(species_metadata, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
