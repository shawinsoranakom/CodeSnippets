def test_get_database_version(self):
        with patch.object(BaseDatabaseWrapper, "__init__", return_value=None):
            msg = (
                "subclasses of BaseDatabaseWrapper may require a "
                "get_database_version() method."
            )
            with self.assertRaisesMessage(NotImplementedError, msg):
                BaseDatabaseWrapper().get_database_version()