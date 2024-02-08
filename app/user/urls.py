"""
URL mappings for the user API.
"""

from django.urls import path, include
from user import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("fetch", views.UserViewSet)

app_name = "user"

urlpatterns = [
    path("create/", views.CreateUserView.as_view(), name="create"),
    path("token/", views.CreateTokenView.as_view(), name="token"),
    path("me/", views.GetUserView.as_view(), name="me"),
    path("", include(router.urls)),
]
