"""
Views for the user API.
"""

import datetime
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
from rest_framework.views import APIView
from core.models import EmailVerificationToken
from core.signals import generate_verification_token


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system."""

    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        """Create a new user."""
        serializer.save(created_by=self.request.user)


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
        "is_verified",
        "approver",
        "created_by",
    )

    def get_queryset(self):
        """Retrieve meta references."""
        return self.queryset.order_by("-id")


class ChangePassword(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        current_password = request.data["current_password"]
        new_password = request.data["new_password"]

        user = request.user
        if not user.check_password(raw_password=current_password):
            return Response(
                {"detail": "password is incorrect"}, status=status.HTTP_400_BAD_REQUEST
            )
        else:
            user.set_password(new_password)
            user.save()
            return Response(
                {"detail": "password changed successfully"}, status=status.HTTP_200_OK
            )


class VerifyEmailView(APIView):

    def get(self, request):
        token = request.GET.get("token")

        try:
            verification_token = EmailVerificationToken.objects.get(token=token)

            if (
                verification_token.expires_at.replace(tzinfo=None)
                < datetime.datetime.now()
            ):
                return Response(
                    {"detail": "Token expired"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not verification_token.user.is_verified:
                verification_token.user.is_verified = True
                verification_token.user.save()
                return Response(
                    {"detail": "Email successfully verified"}, status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "Email already verified"},
                    status=status.HTTP_200_OK,
                )

        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"detail": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


class ResendVerificationEmailView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        try:

            verification_token_model: EmailVerificationToken = (
                user.email_verification_token
            )
            # print(verification_token_model)

            new_token, expires_at = generate_verification_token()
            verification_token_model.token = new_token
            verification_token_model.expires_at = expires_at
            verification_token_model.save()

            return Response(
                {"detail": "Verification email resent"}, status=status.HTTP_200_OK
            )

        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"detail": "Error while attempting to resend"},
                status=status.HTTP_400_BAD_REQUEST,
            )
