def test_migration_path_distributed_namespace(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        test_apps_dir = os.path.join(base_dir, "migrations", "migrations_test_apps")
        expected_msg = (
            "Could not locate an appropriate location to create "
            "migrations package namespace_app.migrations. Make sure the toplevel "
            "package exists and can be imported."
        )
        with extend_sys_path(
            os.path.join(test_apps_dir, "distributed_app_location_1"),
            os.path.join(test_apps_dir, "distributed_app_location_2"),
        ):
            migration = migrations.Migration("0001_initial", "namespace_app")
            writer = MigrationWriter(migration)
            with self.assertRaisesMessage(ValueError, expected_msg):
                writer.path