from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import (
    SpeciesMetadata,
    MetaReference,
)  # Replace with your actual model name


@receiver(post_save, sender=SpeciesMetadata)
def send_update_notification(sender, instance, created, **kwargs):
    # print(f"Your model instance ({instance.id}) has been updated.")
    if not created:  # Only send email if the instance was updated
        subject = "Update Notification for SpeciesMetadata"
        message = f"Your model instance ({instance.id}) has been updated."  # Customize your message
        from_email = settings.EMAIL_HOST_USER  # Your project's email
        # recipient_list = [instance.user.email]  # Assuming your model has a 'user' field
        recipient_list = ["nivasm@mit.edu"]
        send_mail(subject, message, from_email, recipient_list)
        print("Email sent successfully")


@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    print(f"User {user} logged in")


def send_email_test():
    try:
        print("\n\nSignals are working\n\n")
        subject = "Test Email from Django"
        message = "This is a test message."
        from_email = settings.EMAIL_HOST_USER
        recipient_list = ["nivasm@mit.edu"]
        send_mail(subject, message, from_email, recipient_list)
        print("Email sent successfully")
    except Exception as e:
        print(e)
        print("Email not sent")


# print("Signals are working")
# send_email_test()
