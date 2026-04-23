def test_close_match(self):
        self.__class__.databases = {"defualt"}
        message = (
            "test_utils.tests.DatabaseAliasTests.databases refers to 'defualt' which "
            "is not defined in settings.DATABASES. Did you mean 'default'?"
        )
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            self._validate_databases()