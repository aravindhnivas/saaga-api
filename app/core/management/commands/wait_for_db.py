"""
Django command to wait for the database to be available.
"""
import time
from psycopg2 import OperationalError as Psycopg2OpError
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to wait for database"""

    def handle(self, *args, **options):
        """Entry point for command"""
        # Standard output to log message to the screen as the command is first executed.
        self.stdout.write("Waiting for database...")
        # Boolean value to check if the database is ready yet.
        db_up = False
        while db_up is False:
            try:
                # If we call this and the database is not ready, it throws an error that will be caught and the except block will run instead of the next line db_up=True.
                self.check(databases=["default"])
                # If the database is ready, this line will run, and the while loop is done.
                db_up = True
            except (Psycopg2OpError, OperationalError):
                # Print to the screen that we wait for the database because the database is not ready yet.
                self.stdout.write("Database unavailable, waiting 1 second...")
                # Wait for one second and run the while loop again to check if database is ready.
                time.sleep(2)

        # After the while loop is done, log the message that the database is available.
        self.stdout.write(self.style.SUCCESS("Database available!"))
