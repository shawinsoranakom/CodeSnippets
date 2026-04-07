def test_makemigrations_with_custom_name(self):
        """
        makemigrations --name generate a custom migration name.
        """
        with self.temporary_migration_module() as migration_dir:

            def cmd(migration_count, migration_name, *args):
                call_command(
                    "makemigrations",
                    "migrations",
                    "--verbosity",
                    "0",
                    "--name",
                    migration_name,
                    *args,
                )
                migration_file = os.path.join(
                    migration_dir, "%s_%s.py" % (migration_count, migration_name)
                )
                # Check for existing migration file in migration folder
                self.assertTrue(os.path.exists(migration_file))
                with open(migration_file, encoding="utf-8") as fp:
                    content = fp.read()
                    content = content.replace(" ", "")
                return content

            # generate an initial migration
            migration_name_0001 = "my_initial_migration"
            content = cmd("0001", migration_name_0001)
            self.assertIn(
                "dependencies=[]" if HAS_BLACK else "dependencies=[\n]", content
            )

            # importlib caches os.listdir() on some platforms like macOS
            # (#23850).
            if hasattr(importlib, "invalidate_caches"):
                importlib.invalidate_caches()

            # generate an empty migration
            migration_name_0002 = "my_custom_migration"
            content = cmd("0002", migration_name_0002, "--empty")
            if HAS_BLACK:
                template_str = 'dependencies=[\n("migrations","0001_%s"),\n]'
            else:
                template_str = "dependencies=[\n('migrations','0001_%s'),\n]"
            self.assertIn(
                template_str % migration_name_0001,
                content,
            )
            self.assertIn("operations=[]" if HAS_BLACK else "operations=[\n]", content)