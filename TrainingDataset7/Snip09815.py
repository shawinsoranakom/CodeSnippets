def _clone_test_db(self, suffix, verbosity, keepdb=False):
        # CREATE DATABASE ... WITH TEMPLATE ... requires closing connections
        # to the template database.
        self.connection.close()
        self.connection.close_pool()

        source_database_name = self.connection.settings_dict["NAME"]
        target_database_name = self.get_test_db_clone_settings(suffix)["NAME"]
        test_db_params = {
            "dbname": self._quote_name(target_database_name),
            "suffix": self._get_database_create_suffix(template=source_database_name),
        }
        with self._nodb_cursor() as cursor:
            try:
                self._execute_create_test_db(cursor, test_db_params, keepdb)
            except Exception:
                try:
                    if verbosity >= 1:
                        self.log(
                            "Destroying old test database for alias %s..."
                            % (
                                self._get_database_display_str(
                                    verbosity, target_database_name
                                ),
                            )
                        )
                    cursor.execute("DROP DATABASE %(dbname)s" % test_db_params)
                    self._execute_create_test_db(cursor, test_db_params, keepdb)
                except Exception as e:
                    self.log("Got an error cloning the test database: %s" % e)
                    sys.exit(2)