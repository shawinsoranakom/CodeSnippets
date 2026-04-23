def _clone_test_db(self, suffix, verbosity, keepdb=False):
        """
        Internal implementation - duplicate the test db tables.
        """
        raise NotImplementedError(
            "The database backend doesn't support cloning databases. "
            "Disable the option to run tests in parallel processes."
        )