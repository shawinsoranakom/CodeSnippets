def test_setup_databases(self):
        """
        setup_databases() doesn't fail with dummy database backend.
        """
        tested_connections = db.ConnectionHandler({})
        with mock.patch("django.test.utils.connections", new=tested_connections):
            runner_instance = DiscoverRunner(verbosity=0)
            old_config = runner_instance.setup_databases()
            runner_instance.teardown_databases(old_config)