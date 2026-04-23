def test_non_atomic_migration(self):
        """
        Applying a non-atomic migration works as expected.
        """
        executor = MigrationExecutor(connection)
        with self.assertRaisesMessage(RuntimeError, "Abort migration"):
            executor.migrate([("migrations", "0001_initial")])
        self.assertTableExists("migrations_publisher")
        migrations_apps = executor.loader.project_state(
            ("migrations", "0001_initial")
        ).apps
        Publisher = migrations_apps.get_model("migrations", "Publisher")
        self.assertTrue(Publisher.objects.exists())
        self.assertTableNotExists("migrations_book")