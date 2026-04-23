def test_makemigrations_order(self):
        """
        makemigrations should recognize number-only migrations (0001.py).
        """
        module = "migrations.test_migrations_order"
        with self.temporary_migration_module(module=module) as migration_dir:
            if hasattr(importlib, "invalidate_caches"):
                # importlib caches os.listdir() on some platforms like macOS
                # (#23850).
                importlib.invalidate_caches()
            call_command(
                "makemigrations", "migrations", "--empty", "-n", "a", "-v", "0"
            )
            self.assertTrue(os.path.exists(os.path.join(migration_dir, "0002_a.py")))