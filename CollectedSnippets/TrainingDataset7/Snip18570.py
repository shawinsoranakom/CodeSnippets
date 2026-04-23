def test_allows_auto_pk_0(self):
        with mock.MagicMock() as _connection:
            _connection.sql_mode = {"NO_AUTO_VALUE_ON_ZERO"}
            database_features = DatabaseFeatures(_connection)
            self.assertIs(database_features.allows_auto_pk_0, True)