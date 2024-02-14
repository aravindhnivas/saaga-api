from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .models import (
    SpeciesMetadata,
    MetaReference,
)

from_email = settings.EMAIL_HOST_USER


@receiver(post_save, sender=MetaReference)
def send_update_notification(sender, instance, created, **kwargs):
    user = instance.uploaded_by
    if created and not instance.approved and user.approver:
        subject = "[SaagaDb] New reference metadata uploaded for approval"
        message = f"New metadata has been uploaded by {user.name} ({user.email}). Please review and approve it."
        recipient_list = [user.approver.email]
        send_mail(subject, message, from_email, recipient_list)
        # print(f"Email sent successfully to {user.approver.email}")

    if not created and instance.approved:
        # print("Metadata updated and approved")
        subject = "[SaagaDb] Reference metadata approved"
        message = f"Reference metadata ({instance.ref_url}) approved by {user.approver.name} ({user.approver.email})."
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)
        # print(f"Email sent successfully to {user.email}")


@receiver(post_save, sender=SpeciesMetadata)
def send_update_notification(sender, instance, created, **kwargs):
    user = instance.uploaded_by
    species_name = instance.species.iupac_name
    if created and not instance.approved and user.approver:
        subject = "[SaagaDb] New species metadata uploaded for approval"
        message = f"New metadata for {species_name} has been uploaded by {user.name} ({user.email}). Please review and approve it."
        recipient_list = [user.approver.email]
        send_mail(subject, message, from_email, recipient_list)
        # print(f"Email sent successfully to {user.approver.email}")

    if not created and instance.approved:
        # print("Metadata updated and approved")
        subject = "[SaagaDb] Species metadata approved for " + species_name
        message = f"Species metadata for {species_name} approved by {user.approver.name} ({user.approver.email})."
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)
        # print(f"Email sent successfully to {user.email}")


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
