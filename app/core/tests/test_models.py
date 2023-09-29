"""
Test for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
# from core import models


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_successful(self):
        """Test creating a user with an email is successful."""
        email = "test@example.com"
        password = "testpw123"
        name = "test person"
        organization = "test org"
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            name=name,
            organization=organization
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.name, name)
        self.assertEqual(user.organization, organization)
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_new_user_email_normalized(self):
        """Test email is normalized for new users."""
        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.com', 'test4@example.com']
        ]
        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(
                email, 'pw123', 'name123', 'org123')
            self.assertEqual(user.email, expected)

    def test_new_user_no_required_fields_raises_error(self):
        """Test that creating a user without email, name,
        or organization raises an error."""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'pw123', 'name123', 'org123')
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('test@example.com', '', 'name123', 'org123')
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('test@example.com', 'pw123', '', 'org123')
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('test@example.com', 'pw123', 'name123', '')

    def test_create_superuser(self):
        """Test creating a superuser."""
        email = "test@example.com"
        password = "testpw123"
        name = "test person"
        organization = "test org"
        user = get_user_model().objects.create_superuser(
            email=email,
            password=password,
            name=name,
            organization=organization
        )
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
