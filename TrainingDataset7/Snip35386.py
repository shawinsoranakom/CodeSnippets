def test_no_close_match(self):
        self.__class__.databases = {"void"}
        message = (
            "test_utils.tests.DatabaseAliasTests.databases refers to 'void' which is "
            "not defined in settings.DATABASES."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            self._validate_databases()