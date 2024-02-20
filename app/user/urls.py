"""
URL mappings for the user API.
"""

from django.urls import path, include
from user import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("fetch", views.UserViewSet)
# router.register(r"verify-email", views.VerifyEmailViewSet, basename="verify-email")
app_name = "user"

urlpatterns = [
    path("create/", views.CreateUserView.as_view(), name="create"),
    path("token/", views.CreateTokenView.as_view(), name="token"),
    path("me/", views.GetUserView.as_view(), name="me"),
    path(
        "change-password/",
        views.ChangePassword.as_view(),
        name="change-password",
    ),
    path("verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path(
        "resend-verify-email/",
        views.ResendVerificationEmailView.as_view(),
        name="resend-verify-email",
    ),
    path(
        "request-password-reset",
        views.PasswordReset.as_view(),
        name="request-password-reset",
    ),
    path(
        "password-reset/<str:encoded_pk>/<str:token>/",
        views.ResetPasswordAPI.as_view(),
        name="reset-password",
    ),
    path("", include(router.urls)),
]
