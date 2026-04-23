def test_mysql_strict_mode(self):
        def _clean_sql_mode():
            for alias in self.databases:
                if hasattr(connections[alias], "sql_mode"):
                    del connections[alias].sql_mode

        _clean_sql_mode()
        good_sql_modes = [
            "STRICT_TRANS_TABLES,STRICT_ALL_TABLES",
            "STRICT_TRANS_TABLES",
            "STRICT_ALL_TABLES",
        ]
        for sql_mode in good_sql_modes:
            with mock.patch.object(
                connection,
                "mysql_server_data",
                {"sql_mode": sql_mode},
            ):
                self.assertEqual(check_database_backends(databases=self.databases), [])
            _clean_sql_mode()

        bad_sql_modes = ["", "WHATEVER"]
        for sql_mode in bad_sql_modes:
            mocker_default = mock.patch.object(
                connection,
                "mysql_server_data",
                {"sql_mode": sql_mode},
            )
            mocker_other = mock.patch.object(
                connections["other"],
                "mysql_server_data",
                {"sql_mode": sql_mode},
            )
            with mocker_default, mocker_other:
                # One warning for each database alias
                result = check_database_backends(databases=self.databases)
                self.assertEqual(len(result), 2)
                self.assertEqual([r.id for r in result], ["mysql.W002", "mysql.W002"])
            _clean_sql_mode()