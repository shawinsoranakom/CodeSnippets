def test_setup_aliased_default_database(self):
        """
        setup_databases() doesn't fail when 'default' is aliased
        """
        tested_connections = db.ConnectionHandler(
            {"default": {"NAME": "dummy"}, "aliased": {"NAME": "dummy"}}
        )
        with mock.patch("django.test.utils.connections", new=tested_connections):
            runner_instance = DiscoverRunner(verbosity=0)
            old_config = runner_instance.setup_databases()
            runner_instance.teardown_databases(old_config)