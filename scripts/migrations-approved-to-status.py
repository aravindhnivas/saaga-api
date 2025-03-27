from django.apps import apps
from django.conf import settings

# Get the correct User model
User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

# Get the default user for 'processed_by' (update ID if needed)
try:
    default_user = User.objects.get(pk=2)  # Change this ID as needed
except User.DoesNotExist:
    default_user = None

# Loop through all models and update only those that inherit from BaseModel
for model in apps.get_models():
    if hasattr(model, "status") and hasattr(model, "approved") and hasattr(model, "processed_by"):
        # Ensure the model has STATUS_APPROVED and STATUS_PENDING attributes
        if hasattr(model, "STATUS_APPROVED") and hasattr(model, "STATUS_PENDING"):
            instances = model.objects.all()
            for instance in instances:
                instance.status = (
                    model.STATUS_APPROVED if instance.approved else model.STATUS_PENDING
                )
                if instance.approved and not instance.processed_by and default_user:
                    instance.processed_by = default_user
                instance.save(update_fields=["status", "processed_by"])

print("Update completed successfully!")
