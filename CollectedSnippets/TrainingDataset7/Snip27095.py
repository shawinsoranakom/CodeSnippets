def test_makemigrations_default_merge_name(self):
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_conflict"
        ) as migration_dir:
            call_command(
                "makemigrations",
                "migrations",
                merge=True,
                interactive=False,
                stdout=out,
            )
            merge_file = os.path.join(
                migration_dir,
                "0003_merge_0002_conflicting_second_0002_second.py",
            )
            self.assertIs(os.path.exists(merge_file), True)
            with open(merge_file, encoding="utf-8") as fp:
                content = fp.read()
            if HAS_BLACK:
                target_str = '("migrations", "0002_conflicting_second")'
            else:
                target_str = "('migrations', '0002_conflicting_second')"
            self.assertIn(target_str, content)
        self.assertIn("Created new merge migration %s" % merge_file, out.getvalue())