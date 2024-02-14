"""
Views for the user API.
"""

from rest_framework import generics, authentication, permissions, viewsets, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from user.serializers import (
    UserSerializer,
    AuthTokenSerializer,
    ChangePasswordSerializer,
)
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from rest_framework.response import Response
from django_filters import rest_framework as filters


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""

    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user."""

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class GetUserView(generics.RetrieveAPIView):
    """Get the details of the authenciated user."""

    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user


class UserViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = (
        "email",
        "name",
        "organization",
        "is_superuser",
        "is_staff",
        "is_active",
        "approver",
    )

    def get_queryset(self):
        """Retrieve meta references."""
        return self.queryset.order_by("-id")


class ChangePassword(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer

    def put(self, request, id):
        current_password = request.data["current_password"]
        new_password = request.data["new_password"]

        obj = get_user_model().objects.get(pk=id)
        if not obj.check_password(raw_password=current_password):
            return Response(
                {"msg": "password is incorrect"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            obj.set_password(new_password)
            obj.save()
            return Response(
                {"msg": "password changed successfully"}, status=status.HTTP_200_OK
            )
