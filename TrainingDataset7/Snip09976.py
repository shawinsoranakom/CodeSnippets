def setup_worker_connection(self, _worker_id):
        settings_dict = self.get_test_db_clone_settings(_worker_id)
        # connection.settings_dict must be updated in place for changes to be
        # reflected in django.db.connections. Otherwise new threads would
        # connect to the default database instead of the appropriate clone.
        start_method = multiprocessing.get_start_method()
        if start_method == "fork":
            # Update settings_dict in place.
            self.connection.settings_dict.update(settings_dict)
            self.connection.close()
        elif start_method in {"forkserver", "spawn"}:
            alias = self.connection.alias
            connection_str = (
                f"file:memorydb_{alias}_{_worker_id}?mode=memory&cache=shared"
            )
            source_db_name = settings_dict["NAME"]
            source_db = self.connection.Database.connect(
                f"file:{source_db_name}?mode=ro", uri=True
            )
            target_db = sqlite3.connect(connection_str, uri=True)
            source_db.backup(target_db)
            source_db.close()
            # Update settings_dict in place.
            self.connection.settings_dict.update(settings_dict)
            self.connection.settings_dict["NAME"] = connection_str
            # Re-open connection to in-memory database before closing copy
            # connection.
            self.connection.connect()
            target_db.close()