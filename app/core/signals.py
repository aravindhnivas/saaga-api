from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.dispatch import receiver
from .models import SpeciesMetadata, MetaReference
import textwrap
from django.contrib.auth import get_user_model

from_email = settings.EMAIL_HOST_USER
user_model = get_user_model()


@receiver(pre_save, sender=get_user_model())
def set_original_is_staff(sender, instance, **kwargs):
    try:
        original = sender.objects.get(pk=instance.pk)
        instance._original_is_staff = original.is_staff
        instance._original_is_superuser = original.is_superuser
    except sender.DoesNotExist:
        instance._original_is_staff = None


@receiver(post_save, sender=user_model)
def send_update_notification(sender, instance, created, **kwargs):
    message = ""

    if created:
        subject = f"[SaagaDb] {instance.name}: Your account has been created"
        message = textwrap.dedent(
            f"""
            Your account has been created{' (with admin privilege)' if instance.is_staff else ''}.
            Please login to SaagaDb to start using the application.
            http://herzberg.mit.edu/login
            
            Your approver is {instance.approver.name} ({instance.approver.email}).
            The approver will review and approve your data uploads: species- and reference- metadata.
        """
        ).strip()
    else:
        if instance.is_staff and instance.is_staff != instance._original_is_staff:
            subject = (
                f"[SaagaDb] {instance.name}: Your account has been promoted to admin"
            )
            message = textwrap.dedent(
                f"""
                Your account has been promoted to admin.
                You can now approve data uploads: species- and reference- metadata.
            """
            ).strip()

        if (
            instance.is_superuser
            and instance.is_superuser != instance._original_is_superuser
        ):
            subject = f"[SaagaDb] {instance.name}: Your account has been promoted to superuser"
            message = textwrap.dedent(
                f"""
                Your account has been promoted to superuser.
                You can now approve data uploads: species- and reference- metadata.
            """
            ).strip()

    if message:
        recipient_list = [instance.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        print(f"Email sent successfully to {instance.email}")


@receiver(post_save, sender=MetaReference)
def send_update_notification(sender, instance, created, **kwargs):
    user = instance.uploaded_by
    if created and not instance.approved and user.approver:
        subject = f"[SaagaDb] {user.name}: New reference metadata uploaded for approval"
        message = textwrap.dedent(
            f"""
            New metadata has been uploaded by {user.name} ({user.email}).
            Please review and approve it.
            http://herzberg.mit.edu/admin/dashboard/approve-data/{user.id}
        """
        ).strip()
        recipient_list = [user.approver.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        # print(f"Email sent successfully to {user.approver.email}")

    if not created and instance.approved:
        # print("Metadata updated and approved")
        subject = f"[SaagaDb] Reference metadata approved"
        message = f"Reference metadata ({instance.ref.ref_url}) approved by {user.approver.name} ({user.approver.email})."
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        # print(f"Email sent successfully to {user.email}")


@receiver(post_save, sender=SpeciesMetadata)
def send_update_notification(sender, instance, created, **kwargs):
    user = instance.uploaded_by
    species_name = instance.species.iupac_name
    if created and not instance.approved and user.approver:
        subject = f"[SaagaDb] {user.name}: New species metadata uploaded for approval"
        message = textwrap.dedent(
            f"""
            New metadata for {species_name} has been uploaded by {user.name} ({user.email}).
            Please review and approve it.
            http://herzberg.mit.edu/admin/dashboard/approve-data/{user.id}
        """
        ).strip()
        recipient_list = [user.approver.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        # print(f"Email sent successfully to {user.approver.email}")

    if not created and instance.approved:
        # print("Metadata updated and approved")
        subject = "[SaagaDb] Species metadata approved for " + species_name
        message = f"Species metadata for {species_name} approved by {user.approver.name} ({user.approver.email})."
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        # print(f"Email sent successfully to {user.email}")


def send_email_test():
    try:
        print("\n\nSignals are working\n\n")
        subject = "Test Email from Django"
        message = "This is a test message."
        from_email = settings.EMAIL_HOST_USER
        recipient_list = ["nivasm@mit.edu"]
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        print("Email sent successfully")
    except Exception as e:
        print(e)
        print("Email not sent")


# print("Signals are working")
# send_email_test()
