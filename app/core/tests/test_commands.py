"""
Test custom Django management commands
"""
# patch allows mocking of behavior of the database to simulate when the database is returning a response or not.
from unittest.mock import patch

from psycopg2 import OperationalError as Psycopg2Error

# call_command is a helper function provided by Django that allows us to call the command.
from django.core.management import call_command
from django.db.utils import OperationalError
# SimpleTestCase is used because we do not need migrations etc. to be applied to the test. We are just simulating behavior of the database. We use SimpleTestCase so that it does not create any database setup behind the scenes.
from django.test import SimpleTestCase


@patch('core.management.commands.wait_for_db.Command.check')
# Mock the command 'check', or the behavior of the database. 'check' is provided by the BaseCommand class. 'check' is a method that checks the status of the database. Here we simulate the response of the 'check' method.
# Patch adds a new argument to each of the calls as patched_check.
class CommandTests(SimpleTestCase):
    """Test commands."""

    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for database if database ready."""
        # When check is called inside the test case, it returns the true value.
        patched_check.return_value = True
        # Check if the command can be called.
        call_command('wait_for_db')
        # Check if the check method is called with the parameters "databases=['default']".
        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    # Replace the sleep function and just return a None value. We override the behavior of sleep so it does not wait when the unit tests run.
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        """Test waiting for database when getting OperationalError."""
        # Make the check method raise exceptions - Psycopg2Error for the first two times, OperationalError for the next three times, and return true value at last.
        patched_check.side_effect = [Psycopg2Error] * 2 + \
            [OperationalError] * 3 + [True]

        # When wait_for_db command is called, the check method will raise exceptions or return values according to those defined using patched_check.side_effect.
        call_command('wait_for_db')

        # Make sure the check method is called six times as defined by patched_check.side_effect.
        self.assertEqual(patched_check.call_count, 6)

        # Check if the check method is called with the parameters "databases=['default']".
        patched_check.assert_called_with(databases=['default'])
