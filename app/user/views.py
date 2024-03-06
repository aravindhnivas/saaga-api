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
    EmailSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.mail import send_mail
from rest_framework.response import Response
from django_filters import rest_framework as filters
from rest_framework.views import APIView
from core.models import EmailVerificationToken
from core.signals import generate_verification_token
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.exceptions import PermissionDenied


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


class UserViewSet(viewsets.ModelViewSet):

    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.IsAdminUser]
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

    http_method_names = ["get", "patch", "head"]

    # def get_permissions(self):
    #     """Return appropriate permissions based on action."""
    #     if self.request.method in ["PATCH"]:
    #         permission_classes = [permissions.IsAdminUser]
    #     else:
    #         permission_classes = [permissions.IsAuthenticated]
    #     return [permission() for permission in permission_classes]

    def get_queryset(self):
        """Retrieve meta references."""
        return self.queryset.order_by("-id")

    def perform_update(self, serializer):
        """Update an existing user."""
        if not self.request.user.is_superuser:
            raise PermissionDenied("You are not authorized to perform this action.")
        serializer.save()


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


class PasswordReset(generics.GenericAPIView):
    """
    Request for Password Reset Link.
    """

    serializer_class = EmailSerializer

    def post(self, request):
        """
        Create token.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.data["email"]
        user = get_user_model().objects.filter(email=email).first()

        if user:
            encoded_pk = urlsafe_base64_encode(force_bytes(user.pk))
            token = PasswordResetTokenGenerator().make_token(user)

            print(f"{user=}, {encoded_pk=}, {token=}")
            reset_url = reverse(
                "user:reset-password",
                kwargs={"encoded_pk": encoded_pk, "token": token},
            )
            reset_link = f"{settings.FRONTEND_URL}/password-reset/{encoded_pk}/{token}/"
            print(reset_link)
            # send the rest_link as mail to the user.

            # send email
            subject = "Password Reset"
            message = f"Your password reset link: {reset_link}"
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=True)

            return Response(
                {"message": f"Your password rest link: {reset_link}"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "User doesn't exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResetPasswordAPI(generics.GenericAPIView):
    """
    Verify and Reset Password Token View.
    """

    serializer_class = ResetPasswordSerializer

    def patch(self, request, *args, **kwargs):
        """
        Verify token & encoded_pk and then reset the password.
        """
        serializer = self.serializer_class(
            data=request.data, context={"kwargs": kwargs}
        )

        serializer.is_valid(raise_exception=True)

        return Response(
            {"message": "Password reset complete"},
            status=status.HTTP_200_OK,
        )
