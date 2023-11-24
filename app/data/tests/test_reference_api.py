"""
Test for reference APIs.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Reference
import tempfile
import os


def create_reference(**params):
    """Helper function to create a reference."""
    defaults = {
        'doi': '10.1021/acs.jcim.0c00128',
        'ref_url': 'https://doi.org/10.1021/acs.jcim.0c00128',
        'bibtex': 'bibtex_file',
        'notes': 'Test reference',
    }
    defaults.update(params)

    return Reference.objects.create(**defaults)


class PublicReferenceApiTests(TestCase):
    """Test the publicly available reference API."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required_for_post(self):
        """Test that authentication is required for post creating references."""
        url = reverse('data:reference-list')
        payload = {
            'doi': '10.1021/acs.jcim.0c00128',
            'ref_url': 'https://doi.org/10.1021/acs.jcim.0c00128',
            'bibtex': 'bibtex_file',
            'notes': 'Test reference'}

        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_for_put(self):
        """Test that authentication is required for put updating references."""
        reference = create_reference()
        url = reverse('data:reference-detail', args=[reference.id])
        payload = {
            'doi': '10.1021/acs.jcim.0c00128',
            'ref_url': 'https://doi.org/10.1021/acs.jcim.0c00128',
            'bibtex': 'bibtex_file',
            'notes': 'Test reference put',
            '_change_reason': 'Test change reason'}

        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_for_patch(self):
        """Test that authentication is required for patch updating references."""
        reference = create_reference()
        url = reverse('data:reference-detail', args=[reference.id])
        payload = {'doi': 'new doi', '_change_reason': 'Test change reason'}

        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_for_delete(self):
        """Test that authentication is required for deleting references."""
        reference = create_reference()
        url = reverse('data:reference-detail',
                      args=[reference.id]) + '?delete_reason=Test delete reason'

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_reference_list(self):
        """Test getting a list of references."""
        create_reference(ref_url='url1')
        create_reference(ref_url='url2')
        url = reverse('data:reference-list')

        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_get_reference_detail(self):
        """Test getting a reference detail."""
        reference = create_reference()
        url = reverse('data:reference-detail', args=[reference.id])

        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class PrivateReferenceApiTests(TestCase):
    """Test the private reference API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='example@example.com',
            password='testpass',
            name='Test User',
            organization='Test Organization')
        self.client.force_authenticate(self.user)

    def test_create_reference(self):
        """Test creating a reference."""
        url = reverse('data:reference-list')
        with tempfile.NamedTemporaryFile(suffix='.bib') as bib_file:
            bib_file.write(b'@article{test, title={Test}}')
            bib_file.seek(0)
            payload = {
                'doi': 'test doi',
                'ref_url': 'test url',
                'bibtex': bib_file,
                'notes': 'Test reference'}
            res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        reference = Reference.objects.get(id=res.data['id'])
        for k, v in payload.items():
            if k != 'bibtex':
                self.assertEqual(v, getattr(reference, k))
        self.assertIn('bibtex', res.data)
        self.assertTrue(os.path.exists(reference.bibtex.path))
        history_exists = Reference.history.filter(
            id=reference.id).exists()
        self.assertTrue(history_exists)
        reference.bibtex.delete()

    def test_create_reference_with_existing_url(self):
        """Test creating a reference with an existing ref_url."""
        create_reference(ref_url='test url')
        url = reverse('data:reference-list')
        with tempfile.NamedTemporaryFile(suffix='.bib') as bib_file:
            bib_file.write(b'@article{test, title={Test}}')
            bib_file.seek(0)
            payload = {
                'doi': 'test doi',
                'ref_url': 'test url',
                'bibtex': bib_file,
                'notes': 'Test reference'}
            res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reference_with_invalid_bibtex(self):
        """Test creating a reference with an invalid bibtex file."""
        url = reverse('data:reference-list')
        payload = {
            'doi': 'test doi',
            'ref_url': 'test url',
            'bibtex': 'invalid bibtex file',
            'notes': 'Test reference'}
        res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_partial_update(self):
        """Test updating a reference with patch."""
        reference = create_reference(ref_url='url')
        url = reverse('data:reference-detail', args=[reference.id])
        payload = {'doi': 'new doi', '_change_reason': 'Test change reason'}
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        reference.refresh_from_db()
        for k, v in payload.items():
            if k != '_change_reason':
                self.assertEqual(v, getattr(reference, k))
        history_count = Reference.history.filter(id=reference.id).count()
        self.assertEqual(history_count, 2)

    def test_full_update(self):
        """Test updating a reference with put."""
        reference = create_reference(ref_url='Original reference')
        url = reverse('data:reference-detail', args=[reference.id])
        with tempfile.NamedTemporaryFile(suffix='.bib') as bib_file:
            bib_file.write(b'@article{test, title={Test}}')
            bib_file.seek(0)
            payload = {'doi': 'Updated doi',
                       'ref_url': 'Updated reference',
                       'bibtex': bib_file,
                       'notes': 'Updated notes',
                       '_change_reason': 'Test change reason'}
            res = self.client.put(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        reference.refresh_from_db()
        for k, v in payload.items():
            if k not in ['_change_reason', 'bibtex']:
                self.assertEqual(v, getattr(reference, k))
        self.assertTrue(os.path.exists(reference.bibtex.path))
        history_count = Reference.history.filter(id=reference.id).count()
        self.assertEqual(history_count, 2)
        reference.bibtex.delete()

    def test_delete_reference(self):
        """Test deleting a reference."""
        reference = create_reference()
        url = reverse('data:reference-detail', args=[reference.id]) + \
            '?delete_reason=Test delete reason'
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Reference.objects.filter(id=reference.id).exists())
        history_count = Reference.history.filter(id=reference.id).count()
        self.assertEqual(history_count, 2)
