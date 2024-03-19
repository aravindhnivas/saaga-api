from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.forms.models import model_to_dict


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["user_approvers"] = list(
            user.approver.all().values_list("name", flat=True)
        )

        token["user"] = model_to_dict(
            user,
            fields=[
                "id",
                "name",
                "email",
                "organization",
                "is_staff",
                "is_superuser",
                "is_active",
            ],
        )

        return token
