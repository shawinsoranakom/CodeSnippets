def _clone_test_db(self, suffix, verbosity, keepdb=False):
        source_database_name = self.connection.settings_dict["NAME"]
        target_database_name = self.get_test_db_clone_settings(suffix)["NAME"]
        if not self.is_in_memory_db(source_database_name):
            # Erase the old test database
            if os.access(target_database_name, os.F_OK):
                if keepdb:
                    return
                if verbosity >= 1:
                    self.log(
                        "Destroying old test database for alias %s..."
                        % (
                            self._get_database_display_str(
                                verbosity, target_database_name
                            ),
                        )
                    )
                try:
                    os.remove(target_database_name)
                except Exception as e:
                    self.log("Got an error deleting the old test database: %s" % e)
                    sys.exit(2)
            try:
                shutil.copy(source_database_name, target_database_name)
            except Exception as e:
                self.log("Got an error cloning the test database: %s" % e)
                sys.exit(2)
        # Forking automatically makes a copy of an in-memory database.
        # Forkserver and spawn require migrating to disk which will be
        # re-opened in setup_worker_connection.
        elif multiprocessing.get_start_method() in {"forkserver", "spawn"}:
            ondisk_db = sqlite3.connect(target_database_name, uri=True)
            self.connection.connection.backup(ondisk_db)
            ondisk_db.close()