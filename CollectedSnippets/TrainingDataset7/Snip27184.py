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