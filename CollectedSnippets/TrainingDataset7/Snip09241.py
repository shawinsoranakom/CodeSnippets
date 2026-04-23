def setup_worker_connection(self, _worker_id):
        settings_dict = self.get_test_db_clone_settings(str(_worker_id))
        # connection.settings_dict must be updated in place for changes to be
        # reflected in django.db.connections. If the following line assigned
        # connection.settings_dict = settings_dict, new threads would connect
        # to the default database instead of the appropriate clone.
        self.connection.settings_dict.update(settings_dict)
        self.connection.close()