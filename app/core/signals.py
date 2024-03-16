# import datetime
import textwrap
import secrets
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.dispatch import receiver
from .models import SpeciesMetadata, MetaReference, EmailVerificationToken
from .models import user_saved_with_approvers
from django.contrib.auth import get_user_model
from django.utils import timezone


def generate_verification_token():
    """Generates a unique, random token"""
    token = secrets.token_urlsafe(32)  # Adjust token length as needed
    # expires_at = datetime.datetime.now() + datetime.timedelta(minutes=30)
    expires_at = timezone.now() + timezone.timedelta(minutes=30)
    return token, expires_at


from_email = settings.EMAIL_HOST_USER
User = get_user_model()


@receiver(post_save, sender=EmailVerificationToken)
def send_verification_email(sender, instance, created, **kwargs):

    user = instance.user
    token = instance.token

    if not created:
        subject = f"[SaagaDb] Verify your email"
        message = f"Click the link below to verify your email: \n{settings.FRONTEND_URL}/api/user/verify-email/?token={token}"
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)


@receiver(pre_save, sender=User)
def set_original_is_staff(sender, instance, **kwargs):
    try:
        original = sender.objects.get(pk=instance.pk)
        instance._original_is_staff = original.is_staff
        instance._original_is_superuser = original.is_superuser
    except sender.DoesNotExist:
        instance._original_is_staff = None


# @receiver(post_save, sender=User)
@receiver(user_saved_with_approvers)
def user_created_signal(sender, instance, created, **kwargs):
    message = ""
    if not instance.approver:
        print("Approver not set")
        return

    approvers_info = []
    for approver in instance.approver.all():
        approvers_info.append(f"{approver.name} ({approver.email})")

    approvers_string = ", ".join(approvers_info)
    token, expires_at = generate_verification_token()  # Generate the token here
    EmailVerificationToken.objects.create(
        user=instance, token=token, expires_at=expires_at
    )

    subject = f"[SaagaDb] {instance.name}: Your account has been created"
    message = textwrap.dedent(
        f"""
        Your account has been created{' (with admin privilege)' if instance.is_staff else ''}.
        Please login to SaagaDb to start using the application.
        http://herzberg.mit.edu/login
        
        Your approver(s) is {approvers_string if approvers_string else 'None'}.
        The approver will review and approve your data uploads: species- and reference- metadata.'
        
        To start using the application, please verify your email by clicking the link below:
        {settings.FRONTEND_URL}/api/user/verify-email/?token={token}"""
    ).strip()

    if message:
        recipient_list = [instance.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        print(f"Email sent successfully to {instance.email}")


@receiver(post_save, sender=User)
def user_updated_signal(sender, instance, created, **kwargs):
    message = ""
    if not created:
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
def send_meta_ref_update_notification(sender, instance, created, **kwargs):
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
        recipient_list = user.approver.values_list("email", flat=True)
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        print(f"Email sent successfully to {', '.join(recipient_list)}")

    if not created and instance.approved:
        subject = f"[SaagaDb] Reference metadata approved"
        message = f"Reference metadata ({instance.ref.ref_url}) approved."
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        print(f"Email sent successfully to {user.email}")


@receiver(post_save, sender=SpeciesMetadata)
def send_meta_species_update_notification(sender, instance, created, **kwargs):
    user = instance.uploaded_by

    if not user or not user.approver:
        print("User or approver not set for the metadata. Skipping email notification.")
        return

    species_name = instance.species.iupac_name

    # if created and not instance.approved and user.approver:
    # subject = f"[SaagaDb] {user.name}: New species metadata uploaded for approval"
    # message = textwrap.dedent(
    #     f"""
    #     New metadata for {species_name} has been uploaded by {user.name} ({user.email}).
    #     Please review and approve it.
    #     http://herzberg.mit.edu/admin/dashboard/approve-data/{user.id}
    # """
    # ).strip()
    # recipient_list = user.approver.values_list("email", flat=True)
    # send_mail(subject, message, from_email, recipient_list, fail_silently=True)

    # print(f"Email sent successfully to {', '.join(recipient_list)}")

    if not created and instance.approved:
        subject = "[SaagaDb] Species metadata approved for " + species_name
        message = f"Species metadata for {species_name} approved."
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list, fail_silently=True)
        print(f"Email sent successfully to {user.email}")


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
