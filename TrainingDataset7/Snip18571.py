def test_allows_group_by_selected_pks(self):
        with mock.MagicMock() as _connection:
            _connection.mysql_is_mariadb = False
            database_features = DatabaseFeatures(_connection)
            self.assertIs(database_features.allows_group_by_selected_pks, True)

        with mock.MagicMock() as _connection:
            _connection.mysql_is_mariadb = False
            _connection.sql_mode = {}
            database_features = DatabaseFeatures(_connection)
            self.assertIs(database_features.allows_group_by_selected_pks, True)

        with mock.MagicMock() as _connection:
            _connection.mysql_is_mariadb = True
            _connection.sql_mode = {"ONLY_FULL_GROUP_BY"}
            database_features = DatabaseFeatures(_connection)
            self.assertIs(database_features.allows_group_by_selected_pks, False)