def _destroy_test_db(self, test_database_name, verbosity):
        self.connection.close_pool()
        return super()._destroy_test_db(test_database_name, verbosity)