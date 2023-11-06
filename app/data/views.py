"""
Views for data APIs.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django_rdkit.models import *
from core.models import Species, Linelist, SpeciesMetadata, Reference, MetaReference, Line
from data import serializers
from rdkit import Chem
from rdkit.Chem import Descriptors
import json
import selfies as sf
from django.db.models import ProtectedError
from django.utils.translation import gettext_lazy as _
import requests
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes, extend_schema_view
from django.http import FileResponse
import io
from data.parse_metadata import read_intfile, read_varfile, read_qpartfile
from data.parse_line import parse_cat
from django.core.exceptions import ValidationError


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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # if protected, cannot be deleted, show error message
        except ProtectedError as exception:
            message = f"Cannot delete as linelist({str(instance)}) is being referenced through protected foreign key"
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {"type": str(type(exception)), "message": message},
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)


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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # if protected, cannot be deleted, show error message
        except ProtectedError as exception:
            message = f"Cannot delete as {str(instance)} is being referenced through protected foreign key"
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {"type": str(type(exception)), "message": message},
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(list=extend_schema(parameters=[OpenApiParameter("substruct", OpenApiTypes.STR, description="Filter species by substructure")]))
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
        """Retrieve species"""
        substruct = self.request.query_params.get('substruct')
        if substruct:
            return self.queryset.filter(mol_obj__hassubstruct=QMOL(Value(substruct))).order_by('-id')
        return self.queryset.order_by('-id')

    def perform_create(self, serializer):
        """Create a new species."""
        received_json = json.dumps(self.request.data)
        json_dict = json.loads(received_json)
        smiles = json_dict['smiles']
        canonical_smiles = Chem.CanonSmiles(smiles)
        selfies_string = sf.encoder(canonical_smiles)
        rdkit_mol_obj = Chem.MolFromSmiles(canonical_smiles)
        molecular_mass = Descriptors.ExactMolWt(rdkit_mol_obj)
        serializer.save(entry_staff=self.request.user, mol_obj=rdkit_mol_obj,
                        smiles=canonical_smiles, selfies=selfies_string, molecular_mass=molecular_mass)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # if protected, cannot be deleted, show error message
        except ProtectedError as exception:
            message = f"Cannot delete as {str(instance)} is being referenced through protected foreign key"
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {"type": str(type(exception)), "message": message},
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)


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

    def create(self, request, *args, **kwargs):
        """Create a new species metadata."""
        serializer = self.get_serializer(data=request.data)
        int_file = request.FILES.get('int_file')
        var_file = request.FILES.get('var_file')
        qpart_file = request.FILES.get('qpart_file')
        try:
            partition_dict = read_qpartfile(qpart_file)
        except ValueError:
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {"type": "ValueError", "message": "Partition function does not contain 300.000 K"},
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)
        if serializer.is_valid():
            if int_file and var_file:
                mu_a, mu_b, mu_c = read_intfile(int_file)
                a_const, b_const, c_const = read_varfile(var_file)
                serializer.save(entry_staff=request.user, mu_a=mu_a, mu_b=mu_b,
                                mu_c=mu_c, a_const=a_const, b_const=b_const, c_const=c_const, partition_function=partition_dict)
            elif int_file:
                mu_a, mu_b, mu_c = read_intfile(int_file)
                serializer.save(entry_staff=request.user, mu_a=mu_a, mu_b=mu_b,
                                mu_c=mu_c, partition_function=partition_dict)
            elif var_file:
                a_const, b_const, c_const = read_varfile(var_file)
                serializer.save(entry_staff=request.user,
                                a_const=a_const, b_const=b_const, c_const=c_const, partition_function=partition_dict)
            else:
                serializer.save(entry_staff=request.user,
                                partition_function=partition_dict)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # if protected, cannot be deleted, show error message
        except ProtectedError as exception:
            message = f"Cannot delete as {str(instance)} is being referenced through protected foreign key"
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {"type": str(type(exception)), "message": message},
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)


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
    queryset = Line.objects.all()
    serializer_class = serializers.LineSerializer
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

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'query':
            return serializers.QuerySerializer
        return self.serializer_class

    def create(self, request, *args, **kwargs):
        """Create a line."""
        meta_id = request.data['meta']
        measured = request.data['measured']
        lower_state_qn = request.data['lower_state_qn']
        upper_state_qn = request.data['upper_state_qn']
        rovibrational = request.data['rovibrational']
        vib_qn = request.data['vib_qn']
        notes = request.data['notes']
        cat_file = request.FILES.get('cat_file')
        meta_obj = SpeciesMetadata.objects.get(id=meta_id)
        qpart_file = meta_obj.qpart_file.open('r')
        frequency, uncertainty, intensity, s_ij_mu2, a_ij, lower_state_energy, upper_state_energy, \
            lower_state_degeneracy, upper_state_degeneracy, pickett_qn_code, \
            pickett_lower_state_qn, pickett_upper_state_qn = parse_cat(
                cat_file, qpart_file=qpart_file)
        input_dict_list = []
        for i in range(len(frequency)):
            input_dict_list.append({'meta': meta_id, 'measured': measured, 'frequency': frequency[i], 'uncertainty': uncertainty[i],
                                    'intensity': intensity[i], 's_ij': None, 's_ij_mu2': s_ij_mu2[i], 'a_ij': a_ij[i],
                                    'lower_state_energy': lower_state_energy[i], 'upper_state_energy': upper_state_energy[i],
                                    'lower_state_degeneracy': lower_state_degeneracy[i], 'upper_state_degeneracy': upper_state_degeneracy[i],
                                    'lower_state_qn': lower_state_qn, 'upper_state_qn': upper_state_qn,
                                    'rovibrational': rovibrational, 'vib_qn': vib_qn, 'pickett_qn_code': pickett_qn_code[i],
                                    'pickett_lower_state_qn': pickett_lower_state_qn[i], 'pickett_upper_state_qn': pickett_upper_state_qn[i],
                                    'entry_staff': request.user.id, 'notes': notes, 'cat_file': cat_file})
        # print(input_dict_list)
        # if serializer.is_valid():
        serializer = serializers.LineSerializerList(
            data=input_dict_list)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter("min_freq", OpenApiTypes.STR,
                             description="Filter lines with frequency greater than or equal to this value"),
            OpenApiParameter("max_freq", OpenApiTypes.STR,
                             description="Filter lines with frequency less than or equal to this value")
        ]
    )
    @action(methods=['GET'], detail=False, url_path='query')
    def query(self, request):
        min_freq = request.query_params.get('min_freq')
        max_freq = request.query_params.get('max_freq')
        queryset = self.get_queryset()
        if min_freq and max_freq:
            queryset = queryset.filter(
                frequency__gte=min_freq, frequency__lte=max_freq)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': _('No min_freq or max_freq provided')}, status=status.HTTP_400_BAD_REQUEST)
