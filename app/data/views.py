"""
Views for data APIs.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from core.models import Species, Linelist, SpeciesMetadata, Reference, MetaReference, Line
from data import serializers
from rdkit import Chem
import json
import selfies as sf
from django.db.models import ProtectedError
from django.utils.translation import gettext_lazy as _
import requests
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes
from django.http import FileResponse
import io


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


class ReferenceViewSet(viewsets.ModelViewSet):
    """View for reference APIs."""
    serializer_class = serializers.ReferenceSerializer
    queryset = Reference.objects.all()
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve references."""
        return self.queryset.order_by('-id')

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'upload_file':
            return serializers.BibFileSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new reference."""
        serializer.save(entry_staff=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-file')
    def upload_file(self, request, pk=None):
        """Upload a file to reference."""
        reference = self.get_object()
        serializer = self.get_serializer(reference, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    @extend_schema(
        parameters=[
            OpenApiParameter("bibtex_ids", OpenApiTypes.STR,
                             description="Comma-separated list of bibtex ids to merge")
        ]
    )
    @action(methods=['GET'], detail=False, url_path='bibtex')
    def get_bibtex(self, request):
        """Output bibtex file of choosing."""
        bibtex_ids = request.query_params.get('bibtex_ids')
        queryset = self.get_queryset()
        if bibtex_ids:
            bibtex_ids = self._params_to_ints(bibtex_ids)
            queryset = queryset.filter(id__in=bibtex_ids)
            merged_data = ""
            for entry in queryset:
                with entry.bibtex.open('r') as f:
                    read_data = f.read()
                    merged_data += read_data
                    merged_data += "\n"
            buffer = io.BytesIO()
            buffer.write(bytes(merged_data, 'utf-8'))
            buffer.seek(io.SEEK_SET)
            return FileResponse(buffer, as_attachment=False, filename=f'merged{bibtex_ids}.bib')
        else:
            return Response({'error': _('No bibtex_ids provided')}, status=status.HTTP_400_BAD_REQUEST)


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
        selfies_string = sf.encoder(canonical_smiles)
        rdkit_mol_obj = Chem.MolFromSmiles(canonical_smiles)
        serializer.save(entry_staff=self.request.user, mol_obj=rdkit_mol_obj,
                        smiles=canonical_smiles, selfies=selfies_string)


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


class MetaReferenceViewSet(viewsets.ModelViewSet):
    """View for meta reference APIs."""
    serializer_class = serializers.MetaReferenceSerializer
    queryset = MetaReference.objects.all()
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve meta references."""
        return self.queryset.order_by('-id')

    def perform_create(self, serializer):
        """Create a new meta reference."""
        serializer.save(entry_staff=self.request.user)


class LineViewSet(viewsets.ModelViewSet):
    """View for line APIs."""
    serializer_class = serializers.LineSerializer
    queryset = Line.objects.all()
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve line."""
        return self.queryset.order_by('-id')

    def perform_create(self, serializer):
        """Create a line."""
        serializer.save(entry_staff=self.request.user)
