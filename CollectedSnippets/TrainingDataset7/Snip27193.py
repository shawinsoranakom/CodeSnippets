def test_atomic_operation_in_non_atomic_migration(self):
        """
        An atomic operation is properly rolled back inside a non-atomic
        migration.
        """
        executor = MigrationExecutor(connection)
        with self.assertRaisesMessage(RuntimeError, "Abort migration"):
            executor.migrate([("migrations", "0001_initial")])
        migrations_apps = executor.loader.project_state(
            ("migrations", "0001_initial")
        ).apps
        Editor = migrations_apps.get_model("migrations", "Editor")
        self.assertFalse(Editor.objects.exists())
        # Record previous migration as successful.
        executor.migrate([("migrations", "0001_initial")], fake=True)
        # Rebuild the graph to reflect the new DB state.
        executor.loader.build_graph()
        # Migrating backwards is also atomic.
        with self.assertRaisesMessage(RuntimeError, "Abort migration"):
            executor.migrate([("migrations", None)])
        self.assertFalse(Editor.objects.exists())