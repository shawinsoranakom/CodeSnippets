def test_failing_migration(self):
        # If a migration fails to serialize, it shouldn't generate an empty
        # file. #21280
        apps.register_model("migrations", UnserializableModel)

        with self.temporary_migration_module() as migration_dir:
            with self.assertRaisesMessage(ValueError, "Cannot serialize"):
                call_command("makemigrations", "migrations", verbosity=0)

            initial_file = os.path.join(migration_dir, "0001_initial.py")
            self.assertFalse(os.path.exists(initial_file))