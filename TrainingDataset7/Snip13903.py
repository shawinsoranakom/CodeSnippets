def _post_teardown(self):
        """
        Perform post-test things:
        * Flush the contents of the database to leave a clean slate. If the
          class has an 'available_apps' attribute, don't fire post_migrate.
        * Force-close the connection so the next test gets a clean cursor.
        """
        try:
            self._fixture_teardown()
            super()._post_teardown()
            if self._should_reload_connections():
                # Some DB cursors include SQL statements as part of cursor
                # creation. If you have a test that does a rollback, the effect
                # of these statements is lost, which can affect the operation
                # of tests (e.g., losing a timezone setting causing objects to
                # be created with the wrong time). To make sure this doesn't
                # happen, get a clean connection at the start of every test.
                for conn in connections.all(initialized_only=True):
                    conn.close()
        finally:
            if self.__class__.available_apps is not None:
                apps.unset_available_apps()
                self.__class__._available_apps_calls_balanced -= 1
                setting_changed.send(
                    sender=settings._wrapped.__class__,
                    setting="INSTALLED_APPS",
                    value=settings.INSTALLED_APPS,
                    enter=False,
                )