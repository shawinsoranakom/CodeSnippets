def test_makemigrations_no_init_ambiguous(self):
        """
        Migration directories without an __init__.py file are not allowed if
        there are multiple namespace search paths that resolve to them.
        """
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_no_init"
        ) as migration_dir:
            # Copy the project directory into another place under sys.path.
            app_dir = Path(migration_dir).parent
            os.remove(app_dir / "__init__.py")
            project_dir = app_dir.parent
            dest = project_dir.parent / "other_dir_in_path"
            shutil.copytree(project_dir, dest)
            with extend_sys_path(str(dest)):
                call_command("makemigrations", stdout=out)
        self.assertEqual("No changes detected\n", out.getvalue())