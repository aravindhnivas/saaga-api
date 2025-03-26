"""
Views for data APIs.
"""

import textwrap
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from core.models import BaseModel
# from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_rdkit.models import QMOL, Value  # noqa: F403
from core.models import (
    Species,
    Linelist,
    SpeciesMetadata,
    SpeciesMetadataMiscFileUpload,
    Reference,
    MetaReference,
    Line,
)
from data import serializers
from rdkit import Chem
from rdkit.Chem import Descriptors
import selfies as sf
from django.db.models import ProtectedError
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
    extend_schema_view,
)
from django.http import FileResponse
import io
from data.parse_metadata import read_intfile, read_varfile, read_qpartfile
from data.parse_line import parse_cat
from django_filters import rest_framework as filters
from drf_multiple_model.views import ObjectMultipleModelAPIView
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.parsers import MultiPartParser


from_email = settings.EMAIL_HOST_USER

class BaseApprovalViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for models inheriting from BaseModel, handling automatic
    setting of 'processed_by' on status change during updates.
    """

    def perform_update(self, serializer):
        """Set processed_by user on status change to approved/rejected."""
        
        # Get the instance *before* potentially popping data
        instance = serializer.instance 
        original_status = instance.status # Get current status from the instance
        
        # Get the incoming status from validated data, if present
        new_status = serializer.validated_data.get('status', original_status) # Default to original if not provided
        
        save_kwargs = {} # Arguments to pass to serializer.save()

        # --- Handle History Change Reason ---
        change_reason = serializer.validated_data.pop('_change_reason', None)
        if change_reason:
             # Set _change_reason on the instance for simple-history
             instance._change_reason = change_reason 
        elif new_status != original_status:
             # Optionally, set a default reason if status changes but no reason given
             instance._change_reason = f"Status changed to {new_status} via API" 

        # --- Handle processed_by ---
        # Set 'processed_by' if the status is *changing* to approved or rejected
        if new_status != original_status and new_status in [BaseModel.STATUS_APPROVED, BaseModel.STATUS_REJECTED]:
            save_kwargs['processed_by'] = self.request.user
        # Optional: Clear 'processed_by' if changing *away* from approved/rejected back to pending
        elif new_status != original_status and new_status == BaseModel.STATUS_PENDING:
             save_kwargs['processed_by'] = None # Explicitly clear

        # Save the serializer, passing any extra kwargs
        serializer.save(**save_kwargs)


class LinelistViewSet(BaseApprovalViewSet):
    """View for linelist APIs."""

    serializer_class = serializers.LinelistSerializer
    queryset = Linelist.objects.all()
    authentication_classes = [JWTAuthentication]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("status", "uploaded_by", "linelist_name")

    def get_permissions(self):
        """No authentication required for GET requests."""
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Create a new linelist and autopopulate uploaded_by and approved field."""
        user = self.request.user
        status = "pending" if not user.is_superuser else "approved"
        processed_by = user if status == "approved" else None
        serializer.save(uploaded_by=user, status=status, processed_by=processed_by)

    def get_queryset(self):
        """Retrieve linelists."""
        return self.queryset.order_by("-id").select_related("uploaded_by")

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action in ["update", "partial_update"]:
            return serializers.LinelistChangeSerializer
        return self.serializer_class

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "delete_reason", OpenApiTypes.STR, description="reason to delete"
            )
        ]
    )
    def destroy(self, request, *args, **kwargs):
        """query param delete_reason must be present for DELETE requests."""
        if "delete_reason" not in self.request.query_params:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="{delete_reason: Invalid Delete Reason}",
            )

        try:
            instance = self.get_object()
            instance._change_reason = self.request.query_params["delete_reason"]
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


class ReferenceFilter(filters.FilterSet):
    doi = filters.CharFilter(method="filter_doi")
    # approved = filters.BooleanFilter()
    status = filters.CharFilter()
    uploaded_by = filters.NumberFilter()
    ref_url = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = Reference
        fields = ["doi", "status", "uploaded_by", "ref_url"]

    def filter_doi(self, queryset, name, value):
        if "doi.org/" in value:
            value = value.split("doi.org/")[1]
        return queryset.filter(Q(doi__icontains=value) | Q(doi__iexact=value))


class ReferenceViewSet(BaseApprovalViewSet):
    """View for reference APIs."""

    serializer_class = serializers.ReferenceSerializer
    queryset = Reference.objects.all()
    authentication_classes = [JWTAuthentication]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ReferenceFilter

    def get_permissions(self):
        """No authentication required for GET requests."""
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve references."""
        return self.queryset.order_by("-id").select_related("uploaded_by")

    def perform_create(self, serializer):
        """Create a new list and autopopulate uploaded_by field."""
        serializer.save(uploaded_by=self.request.user, status="approved", processed_by=self.request.user)

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action in ["update", "partial_update"]:
            return serializers.ReferenceChangeSerializer
        return self.serializer_class

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(",")]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "bibtex_ids",
                OpenApiTypes.STR,
                description="Comma-separated list of bibtex ids to merge",
            )
        ]
    )
    @action(methods=["GET"], detail=False, url_path="bibtex")
    def get_bibtex(self, request):
        """Output bibtex file of choosing."""
        bibtex_ids = request.query_params.get("bibtex_ids")
        queryset = self.get_queryset()
        if bibtex_ids:
            bibtex_ids = self._params_to_ints(bibtex_ids)
            queryset = queryset.filter(id__in=bibtex_ids)
            merged_data = ""
            for entry in queryset:
                with entry.bibtex.open("r") as f:
                    read_data = f.read()
                    merged_data += read_data
                    merged_data += "\n"
            buffer = io.BytesIO()
            buffer.write(bytes(merged_data, "utf-8"))
            buffer.seek(io.SEEK_SET)
            return FileResponse(
                buffer, as_attachment=False, filename=f"merged{bibtex_ids}.bib"
            )
        else:
            return Response(
                {"error": _("No bibtex_ids provided")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "delete_reason", OpenApiTypes.STR, description="reason to delete"
            )
        ]
    )
    def destroy(self, request, *args, **kwargs):
        """query param delete_reason must be present for DELETE requests."""
        if "delete_reason" not in self.request.query_params:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="{delete_reason: Invalid Delete Reason}",
            )

        try:
            instance = self.get_object()
            instance._change_reason = self.request.query_params["delete_reason"]
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # if protected, cannot be deleted, show error message
        except ProtectedError as exception:
            message = f"Cannot delete as reference {str(instance)} is being referenced through protected foreign key"
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {"type": str(type(exception)), "message": message},
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "substruct",
                OpenApiTypes.STR,
                description="Filter species by substructure",
            )
        ]
    )
)
class SpeciesViewSet(BaseApprovalViewSet):
    """View for species APIs."""

    serializer_class = serializers.SpeciesSerializer
    queryset = Species.objects.all()
    authentication_classes = [JWTAuthentication]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("status", "uploaded_by", "selfies", "smiles")

    def get_permissions(self):
        """No authentication required for GET requests."""
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve species"""
        substruct = self.request.query_params.get("substruct")
        if substruct:
            return self.queryset.filter(
                mol_obj__hassubstruct=QMOL(Value(substruct))  # noqa: F405
            ).order_by(
                "-id"
            )  # noqa: F405
        return (
            self.queryset.order_by("-id")
            .select_related("uploaded_by")
            .only("uploaded_by__name")
        )

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action in ["update", "partial_update"]:
            return serializers.SpeciesChangeSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new species and autopopulate molecular mass,
        selfies, and rdkit mol object from canonical smiles."""

        smiles = self.request.data.get("smiles")
        canonical_smiles = Chem.CanonSmiles(smiles)
        selfies_string = sf.encoder(canonical_smiles)
        rdkit_mol_obj = Chem.MolFromSmiles(canonical_smiles)
        molecular_mass = Descriptors.ExactMolWt(rdkit_mol_obj)
        serializer.save(
            mol_obj=rdkit_mol_obj,
            smiles=canonical_smiles,
            selfies=selfies_string,
            molecular_mass=molecular_mass,
            uploaded_by=self.request.user,
            status="approved",
            processed_by=self.request.user,
        )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "delete_reason", OpenApiTypes.STR, description="reason to delete"
            )
        ]
    )
    def destroy(self, request, *args, **kwargs):
        """query param delete_reason must be present for DELETE requests."""
        if "delete_reason" not in self.request.query_params:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="{delete_reason: Invalid Delete Reason}",
            )
        try:
            instance = self.get_object()
            instance._change_reason = self.request.query_params["delete_reason"]
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # if protected, cannot be deleted, show error message
        except ProtectedError as exception:
            message = f"Cannot delete as species {str(instance)} is being referenced through protected foreign key"
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {"type": str(type(exception)), "message": message},
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)


class SpeciesMetadataViewSet(BaseApprovalViewSet):
    """View for species metadata APIs."""

    serializer_class = serializers.SpeciesMetadataSerializer
    queryset = SpeciesMetadata.objects.all()
    authentication_classes = [JWTAuthentication]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = (
        "status",
        "uploaded_by",
        "species",
        "linelist",
        "hyperfine",
        "cat_file_added",
    )

    def get_permissions(self):
        """No authentication required for GET requests."""
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve species metadata."""
        return (
            self.queryset.order_by("-id")
            .select_related("species", "linelist", "uploaded_by")
            .only(
                "species__id",
                "species__name_formula",
                "species__smiles",
                "species__iupac_name",
                "linelist__linelist_name",
                "uploaded_by__name",
            )
        )

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action in ["update", "partial_update"]:
            return serializers.SpeciesMetadataChangeSerializer
        return self.serializer_class

    def create(self, request):
        """Create a new species metadata."""

        serializer = self.get_serializer(data=request.data)

        qpart_file = request.FILES.get("qpart_file")
        if qpart_file.name.split(".")[-1] != "qpart":
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {
                    "type": "ValidationError",
                    "message": "The file you uploaded "
                    "is not a .qpart file. Please upload a .qpart file.",
                },
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)
        # Check that the qpart file contains 300.000 K
        try:
            partition_dict = read_qpartfile(qpart_file)
        except ValueError:
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {
                    "type": "ValueError",
                    "message": "Partition function does not contain 300.000 K",
                },
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        mu_a = mu_b = mu_c = a_const = b_const = c_const = None

        # Commented reading int and var files for now
        # Read the int and var files
        # int_file = request.FILES.get("int_file")
        # var_file = request.FILES.get("var_file")
        # if int_file:
        #     mu_a, mu_b, mu_c = read_intfile(int_file)
        # if var_file:
        #     a_const, b_const, c_const = read_varfile(var_file)

        status = "pending" if not self.request.user.is_superuser else "approved"
        processed_by = self.request.user if status == "approved" else None
        data_to_save = {
            "mu_a": mu_a,
            "mu_b": mu_b,
            "mu_c": mu_c,
            "a_const": a_const,
            "b_const": b_const,
            "c_const": c_const,
            "partition_function": partition_dict,
            "uploaded_by": self.request.user,
            "status": status,
            "processed_by": processed_by,
        }

        # Remove None values from the dictionary
        data_to_save = {k: v for k, v in data_to_save.items() if v is not None}
        serializer.save(**data_to_save)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "delete_reason", OpenApiTypes.STR, description="reason to delete"
            )
        ]
    )
    def destroy(self, request, *args, **kwargs):
        """query param delete_reason must be present for DELETE requests."""
        if "delete_reason" not in self.request.query_params:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="{delete_reason: Invalid Delete Reason}",
            )
        try:
            instance = self.get_object()
            instance._change_reason = self.request.query_params["delete_reason"]
            instance.save()

            # Get the historical instance before deletion
            historical_instance = None
            try:
                historical_instance = instance.history.latest()
            except Exception as e:
                print(f"Error getting historical instance: {e}")
                historical_instance = None

            self.perform_destroy(instance)

            if historical_instance:
                print(historical_instance)
                uploaded_by_user = get_user_model().objects.get(
                    id=historical_instance.uploaded_by_id
                )
                rejected_approver = get_user_model().objects.get(
                    id=historical_instance.history_user_id
                )

                send_mail(
                    subject=f"[SaagaDb] Species metadata ({historical_instance.species.iupac_name}) rejected",
                    message=f"Species metadata ({historical_instance.species.iupac_name}) rejected by {rejected_approver.name} ({rejected_approver.email}) and deleted from database.\nNOTE: All the related meta-references and uploaded cat file data also has been deleted.\nReason for deletion: {historical_instance.history_change_reason}.",
                    from_email=from_email,
                    recipient_list=[uploaded_by_user.email],
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

        # if protected, cannot be deleted, show error message
        except ProtectedError as exception:
            message = f"Cannot delete as species metadata {str(instance)} is being referenced through protected foreign key"
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {"type": str(type(exception)), "message": message},
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)


class SpeciesMetadataMiscFileUploadView(BaseApprovalViewSet):

    queryset = SpeciesMetadataMiscFileUpload.objects.all()
    serializer_class = serializers.SpeciesMetadataMiscFileUploadSerializer
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        """No authentication required for GET requests."""
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve species metadata misc files"""
        return self.queryset.order_by("-id").select_related("uploaded_by", "meta")

    def create(self, request):
        """Create a new species metadata misc file."""

        meta = request.data.get("meta")
        notes = request.data.get("notes")
        misc_file = request.FILES.getlist("misc_file")
        data_dict = []

        for file in misc_file:
            data_dict.append(
                {
                    "meta": meta,
                    "name": file.name,
                    "notes": notes,
                    "misc_file": file,
                }
            )
        serializer = self.serializer_class(data=data_dict, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(uploaded_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MetaReferenceViewSet(BaseApprovalViewSet):
    """View for meta reference APIs."""

    serializer_class = serializers.MetaReferenceSerializer
    queryset = MetaReference.objects.all()
    authentication_classes = [JWTAuthentication]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = (
        "status",
        "uploaded_by",
        "meta",
        "ref",
        "dipole_moment",
        "spectrum",
    )

    def get_permissions(self):
        """No authentication required for GET requests."""
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Create a new list and autopopulate uploaded_by and approved field."""
        
        status = "pending" if not self.request.user.is_superuser else "approved"
        processed_by = self.request.user if status == "approved" else None
        serializer.save(uploaded_by=self.request.user, status=status, processed_by=processed_by)

    def get_queryset(self):
        """Retrieve meta references."""
        return self.queryset.order_by("-id").select_related(
            "uploaded_by", "meta", "ref"
        )

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action in ["update", "partial_update"]:
            return serializers.MetaReferenceChangeSerializer
        return self.serializer_class

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "delete_reason", OpenApiTypes.STR, description="reason to delete"
            )
        ]
    )
    def destroy(self, request, *args, **kwargs):
        """query param delete_reason must be present for DELETE requests."""

        if "delete_reason" not in self.request.query_params:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="{delete_reason: Invalid Delete Reason}",
            )

        instance = self.get_object()
        instance._change_reason = self.request.query_params["delete_reason"]
        instance.save()
        # self.perform_destroy(instance)

        # Get the historical instance before deletion
        historical_instance = None
        try:
            historical_instance = instance.history.latest()
        except Exception as e:
            print(f"Error getting historical instance: {e}")
            historical_instance = None

        self.perform_destroy(instance)

        if historical_instance:
            print(historical_instance)
            uploaded_by_user = get_user_model().objects.get(
                id=historical_instance.uploaded_by_id
            )
            rejected_approver = get_user_model().objects.get(
                id=historical_instance.history_user_id
            )

            send_mail(
                subject=f"[SaagaDb] Meta reference ({historical_instance.meta.species.iupac_name}) rejected",
                message=f"Meta reference ({historical_instance.meta.species.iupac_name}) rejected by {rejected_approver.name} ({rejected_approver.email}) and deleted from database.\nReason for deletion: {historical_instance.history_change_reason}.",
                from_email=from_email,
                recipient_list=[uploaded_by_user.email],
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class DirectReferenceAPI(APIView):
    """View for meta reference APIs."""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ref_url = request.data.get("ref_url")
        ref_obj = Reference.objects.filter(ref_url=ref_url).first()

        # reference_serializer = serializers.ReferenceSerializer(data=request.data)
        if not ref_obj:

            request_data = request.data.copy()
            request_data.pop("notes", None)  # Remove 'notes' key
            reference_serializer = serializers.ReferenceSerializer(data=request_data)

            # reference_serializer = serializers.ReferenceSerializer(data=request.data)
            reference_serializer.is_valid(raise_exception=True)
            # print(f"Saving new reference. {ref_url=}")
            reference_serializer.save(uploaded_by=request.user, status="approved")
            ref_obj = reference_serializer.instance
            # print(f"{reference_serializer.validated_data=}")

        ref_id = ref_obj.id
        # print(f"{ref_id=}")

        data = request.data.copy()  # Make a mutable copy of the QueryDict
        data["ref"] = ref_id  # Append ref_id value to 'ref'

        metareference_serializer = serializers.MetaReferenceSerializer(data=data)
        metareference_serializer.is_valid(raise_exception=True)

        status = "pending" if not request.user.is_superuser else "approved"
        processed_by = request.user if status == "approved" else None
        metareference_serializer.save(uploaded_by=request.user, status=status, processed_by=processed_by)

        meta_ref_obj = metareference_serializer.instance

        # print(f"{metareference_serializer.validated_data=}")

        return Response(
            {
                "id": meta_ref_obj.id,
                "ref": ref_id,
                "meta": meta_ref_obj.meta.id,
                "doi": ref_obj.doi,
                "ref_url": ref_obj.ref_url,
                "dipole_moment": meta_ref_obj.dipole_moment,
                "spectrum": meta_ref_obj.spectrum,
            },
            status=status.HTTP_201_CREATED,
        )


class LineViewSet(viewsets.ModelViewSet):
    """View for line APIs."""

    queryset = Line.objects.all()
    serializer_class = serializers.LineSerializer
    authentication_classes = [JWTAuthentication]

    def get_permissions(self):
        """No authentication required for GET requests."""
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve line."""
        if self.action == "query":
            return self.queryset.order_by("frequency").select_related(
                "meta", "meta__species", "meta__linelist"
            )
        return self.queryset.order_by("-id")

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == "query":
            return serializers.QuerySerializer
        elif self.action in ["update", "partial_update"]:
            return serializers.LineChangeSerializerList
        return self.serializer_class

    def create(self, request):
        """Create a line from .cat file."""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        measured = False  # default measured to false right now
        qn_label_str: str = serializer.data["qn_label_str"]
        contains_rovibrational: bool = serializer.data["contains_rovibrational"]
        vib_qn: str = serializer.data["vib_qn"]
        notes: str = serializer.data["notes"]

        qn_label_list = [x.strip() for x in qn_label_str.split(",")]
        print(f"{serializer.data=}")

        if contains_rovibrational:
            """Check if the .cat file contains rovibrational lines,
            If so, check that the vibrational quantum number label
            is provided."""

            print(f"ROVIBRATIONAL TRANSITION: {vib_qn=}")

            if not vib_qn:
                response_msg = {
                    "code": "server_error",
                    "message": _("Internal server error."),
                    "error": {
                        "type": "ValidationError",
                        "message": "Vibrational quantum number "
                        "label must be provided if rovibrational "
                        "is true",
                    },
                }
                return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)
            if vib_qn not in qn_label_list:
                response_msg = {
                    "code": "server_error",
                    "message": _("Internal server error."),
                    "error": {
                        "type": "ValidationError",
                        "message": "Vibrational quantum number "
                        "label must be in quantum number label string.",
                    },
                }
                return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)
        else:
            if vib_qn:
                response_msg = {
                    "code": "server_error",
                    "message": _("Internal server error."),
                    "error": {
                        "type": "ValidationError",
                        "message": "Vibrational quantum number "
                        "label must be empty if there is no "
                        "rovibrational transition",
                    },
                }
                return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)

        cat_file = request.FILES.get("cat_file")
        if cat_file.name.split(".")[-1] != "cat":
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {
                    "type": "ValidationError",
                    "message": "The file you uploaded "
                    "is not a .cat file. Please upload a .cat file.",
                },
            }

            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)

        meta_id = serializer.data["meta"]
        meta_obj = SpeciesMetadata.objects.get(id=meta_id)
        if meta_obj.cat_file:
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {
                    "type": "ValidationError",
                    "message": "The species metadata you selected already have a cat file.",
                },
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)

        qpart_file = None
        # Check if the corresponding species metadata has a qpart file.
        try:
            qpart_file = meta_obj.qpart_file.open("r")
        except FileNotFoundError:
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {
                    "type": "FileNotFoundError",
                    "message": "The species metadata you "
                    "selected does not have a qpart file. "
                    "Please upload the qpart file.",
                },
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)

        # test response
        # return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)

        # Extract info from the .cat file.
        try:
            (
                frequency,
                uncertainty,
                intensity,
                s_ij_mu2,
                a_ij,
                lower_state_energy,
                upper_state_energy,
                lower_state_degeneracy,
                upper_state_degeneracy,
                pickett_qn_code,
                pickett_lower_state_qn,
                pickett_upper_state_qn,
                lower_state_qn_dict_list,
                upper_state_qn_dict_list,
            ) = parse_cat(cat_file, qn_label_list=qn_label_list, qpart_file=qpart_file)
        except ValueError:
            response_msg = {
                "code": "server_error",
                "message": _("Internal server error."),
                "error": {
                    "type": "ValueError",
                    "message": "Quantum number labels do not match "
                    "the number of quantum numbers in .cat file. "
                    "Please check the labels and try again.",
                },
            }
            return Response(response_msg, status=status.HTTP_400_BAD_REQUEST)

        input_dict_list = []
        if contains_rovibrational:
            """Check if the .cat file contains rovibrational lines,
            If so, determines which particular line contains
            rovibrational transition."""
            for i in range(len(frequency)):
                input_dict_list.append(
                    {
                        "meta": meta_id,
                        "measured": measured,
                        "frequency": format(frequency[i], ".4f"),
                        "uncertainty": format(uncertainty[i], ".4f"),
                        "intensity": format(intensity[i], ".4f"),
                        "s_ij": None,
                        "s_ij_mu2": s_ij_mu2[i],
                        "a_ij": a_ij[i],
                        "lower_state_energy": lower_state_energy[i],
                        "upper_state_energy": upper_state_energy[i],
                        "lower_state_degeneracy": lower_state_degeneracy[i],
                        "upper_state_degeneracy": upper_state_degeneracy[i],
                        "lower_state_qn": lower_state_qn_dict_list[i],
                        "upper_state_qn": upper_state_qn_dict_list[i],
                        "rovibrational": lower_state_qn_dict_list[i][vib_qn]
                        != upper_state_qn_dict_list[i][vib_qn],
                        "vib_qn": vib_qn,
                        "pickett_qn_code": pickett_qn_code[i],
                        "pickett_lower_state_qn": pickett_lower_state_qn[i],
                        "pickett_upper_state_qn": pickett_upper_state_qn[i],
                        "notes": notes,
                    }
                )
        else:
            for i in range(len(frequency)):
                input_dict_list.append(
                    {
                        "meta": meta_id,
                        "measured": measured,
                        "frequency": format(frequency[i], ".4f"),
                        "uncertainty": format(uncertainty[i], ".4f"),
                        "intensity": format(intensity[i], ".4f"),
                        "s_ij": None,
                        "s_ij_mu2": s_ij_mu2[i],
                        "a_ij": a_ij[i],
                        "lower_state_energy": lower_state_energy[i],
                        "upper_state_energy": upper_state_energy[i],
                        "lower_state_degeneracy": lower_state_degeneracy[i],
                        "upper_state_degeneracy": upper_state_degeneracy[i],
                        "lower_state_qn": lower_state_qn_dict_list[i],
                        "upper_state_qn": upper_state_qn_dict_list[i],
                        "rovibrational": False,
                        "vib_qn": vib_qn,
                        "pickett_qn_code": pickett_qn_code[i],
                        "pickett_lower_state_qn": pickett_lower_state_qn[i],
                        "pickett_upper_state_qn": pickett_upper_state_qn[i],
                        "notes": notes,
                    }
                )

        serializer = serializers.LineSerializerList(data=input_dict_list, many=True)
        if serializer.is_valid():
            # saving the cat_file to species_metadata
            print(f"{meta_obj.cat_file=}, {cat_file=}")
            meta_obj.cat_file = cat_file
            meta_obj.vib_qn = vib_qn
            meta_obj.qn_label_str = qn_label_str
            meta_obj.contains_rovibrational = contains_rovibrational
            meta_obj.cat_file_added = True
            meta_obj.save()
            serializer.save()

            # send email to approvers
            subject = f"[SaagaDb] {self.request.user.name}: New species metadata uploaded for approval"
            message = textwrap.dedent(
                f"""
                {'REQUESTED URGENT APPROVAL' if meta_obj.request_immediate_approval else ''}
                New metadata for {meta_obj.species.iupac_name} has been uploaded by {self.request.user.name} ({self.request.user.email}).
                Please review and approve it.
                {settings.FRONTEND_URL}/admin/dashboard/approve-data/{self.request.user.id}
            """
            ).strip()
            recipient_list = self.request.user.approver.values_list("email", flat=True)
            send_mail(subject, message, from_email, recipient_list, fail_silently=True)

            return Response(
                {"detail": "cat file parsed and added to the database"},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "min_freq",
                OpenApiTypes.STR,
                description="Filter lines with "
                "frequency greater than or equal to this value",
            ),
            OpenApiParameter(
                "max_freq",
                OpenApiTypes.STR,
                description="Filter lines with frequency "
                "less than or equal to this value",
            ),
        ]
    )
    @action(methods=["GET"], detail=False, url_path="query")
    def query(self, request):
        """Query lines by frequency range."""
        min_freq = request.query_params.get("min_freq")
        max_freq = request.query_params.get("max_freq")
        queryset = self.get_queryset()
        if min_freq and max_freq:
            queryset = queryset.filter(frequency__gte=min_freq, frequency__lte=max_freq)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif min_freq:
            queryset = queryset.filter(frequency__gte=min_freq)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif max_freq:
            queryset = queryset.filter(frequency__lte=max_freq)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": _("No min_freq and/or max_freq provided")},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "delete_reason", OpenApiTypes.STR, description="reason to delete"
            )
        ]
    )
    def destroy(self, request, *args, **kwargs):
        """query param delete_reason must be present for DELETE requests."""
        if "delete_reason" not in self.request.query_params:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data="{delete_reason: Invalid Delete Reason}",
            )

        instance = self.get_object()
        instance._change_reason = self.request.query_params["delete_reason"]
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MetaRefAndSpeciesViewSet(ObjectMultipleModelAPIView):
    # permission_classes = [IsAdminUser]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("status", "uploaded_by")

    querylist = [
        {
            "queryset": MetaReference.objects.all().select_related(
                "uploaded_by", "meta", "ref"
            ),
            "serializer_class": serializers.MetaReferenceSerializer,
        },
        {
            "queryset": SpeciesMetadata.objects.all()
            .select_related("species", "linelist", "uploaded_by")
            .only(
                "species__id",
                "species__name_formula",
                "species__iupac_name",
                "linelist__linelist_name",
                "uploaded_by__name",
            ),
            "serializer_class": serializers.SpeciesMetadataSerializer,
        },
    ]


# class UploadedDataLengthView(APIView):
#     def get(self, request, user_id: int, format=None):

#         user = (
#             get_user_model()
#             .objects.filter(id=user_id)
#             .prefetch_related(
#                 "species_uploads",
#                 "species_metadata_uploads",
#                 "reference_uploads",
#                 "meta_reference_uploads",
#             )
#             .first()
#         )

#         # Get the current user as approver (just in case the user is an approver for other users)

#         if not user:
#             return Response(status=status.HTTP_404_NOT_FOUND)

#         # current_approver = self.user.first()
#         # Initialize an empty dictionary to hold the unapproved counts for each user
#         unapproved_counts = []

#         if user.is_staff:
#             # get all the user whose approver is current approver
#             dependent_users = user.dependent_users.all()

#             unapproved_counts = dependent_users.values("id", "name").annotate(
#                 species_metadata=Count(
#                     "species_metadata_uploads",
#                     filter=Q(
#                         species_metadata_uploads__approved=False,
#                         species_metadata_uploads__cat_file_added=True,
#                     ),
#                     distinct=True,
#                 ),
#                 meta_reference=Count(
#                     "meta_reference_uploads",
#                     filter=Q(meta_reference_uploads__approved=False),
#                     distinct=True,
#                 ),
#             )

#         total_length_full = {
#             "species": user.species_uploads.count(),
#             "species_metadata": user.species_metadata_uploads.count(),
#             "reference": user.reference_uploads.count(),
#             "meta_reference": user.meta_reference_uploads.count(),
#         }

#         total_length_approved = {
#             "species": user.species_uploads.filter(status="approved").count(),
#             "species_metadata": user.species_metadata_uploads.filter(
#                 status="approved"
#             ).count(),
#             "reference": user.reference_uploads.filter(status="approved").count(),
#             "meta_reference": user.meta_reference_uploads.filter(status="approved").count(),
#         }

#         return Response(
#             {
#                 "full": total_length_full,
#                 "approved": total_length_approved,
#                 "unapproved_counts": list(unapproved_counts),
#             }
#         )
class UploadedDataLengthView(APIView):
    # Assuming authentication and permissions are handled appropriately
    
    def get(self, request, user_id: int, format=None):

        # Use the actual related names generated by %(class)s_uploads
        user = (
            get_user_model()
            .objects.filter(id=user_id)
            .prefetch_related(
                "species_uploads",      # Correct for Species
                "speciesmetadata_uploads", # Correct for SpeciesMetadata (lowercase)
                "reference_uploads",    # Correct for Reference
                "metareference_uploads", # Correct for MetaReference (lowercase)
            )
            .first()
        )

        if not user:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        unapproved_counts = []

        # Note: Checking request.user.is_staff might be more appropriate
        # if this view requires the *requesting* user to be staff
        # rather than the user being looked up (user_id). Adjust if needed.
        if request.user.is_staff and request.user.id == user_id: # Example check: only staff can see their own dependents
             # Or maybe: user.is_staff (if the user being looked up needs to be staff)
            dependent_users = user.dependent_users.all() # Get users this user approves

            unapproved_counts = dependent_users.values("id", "name").annotate(
                # Use correct related_names in annotations
                species_metadata=Count(
                    "speciesmetadata_uploads", # Correct name
                    filter=Q(
                        # Use correct relation name in Q object path
                        speciesmetadata_uploads__status=BaseModel.STATUS_PENDING,
                        speciesmetadata_uploads__cat_file_added=True, # Keep this filter if needed
                    ),
                    distinct=True,
                ),
                meta_reference=Count(
                    "metareference_uploads", # Correct name
                    # Use correct relation name in Q object path
                    filter=Q(metareference_uploads__status=BaseModel.STATUS_PENDING),
                    distinct=True,
                ),
            )
        elif not request.user.is_staff and request.user.id != user_id:
             # Non-staff users cannot view other users' data
             return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)
        # If it's a non-staff user viewing their own data, unapproved_counts remains empty []


        # Use correct related_names to get counts
        total_length_full = {
            "species": user.species_uploads.count(),
            "species_metadata": user.speciesmetadata_uploads.count(), # Correct name
            "reference": user.reference_uploads.count(),
            "meta_reference": user.metareference_uploads.count(), # Correct name
        }

        total_length_pending = { # Changed name from approved to pending for clarity
            "species": user.species_uploads.filter(status=BaseModel.STATUS_PENDING).count(),
            "species_metadata": user.speciesmetadata_uploads.filter(
                status=BaseModel.STATUS_PENDING
            ).count(), # Correct name
            "reference": user.reference_uploads.filter(status=BaseModel.STATUS_PENDING).count(),
            "meta_reference": user.metareference_uploads.filter(status=BaseModel.STATUS_PENDING).count(), # Correct name
        }

        return Response(
            {
                "full": total_length_full,
                "pending": total_length_pending, # Changed key name
                # This key name might be confusing if it only applies to staff viewing dependents
                "unapproved_counts": list(unapproved_counts),
            }
        )