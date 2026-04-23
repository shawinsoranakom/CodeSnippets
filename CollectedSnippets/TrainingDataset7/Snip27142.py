def test_squashmigrations_squashes(self):
        """
        squashmigrations squashes migrations.
        """
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations"
        ) as migration_dir:
            call_command(
                "squashmigrations",
                "migrations",
                "0002",
                interactive=False,
                stdout=out,
                no_color=True,
            )

            squashed_migration_file = os.path.join(
                migration_dir, "0001_squashed_0002_second.py"
            )
            self.assertTrue(os.path.exists(squashed_migration_file))
        self.assertEqual(
            out.getvalue(),
            "Will squash the following migrations:\n"
            " - 0001_initial\n"
            " - 0002_second\n"
            "Optimizing...\n"
            "  Optimized from 8 operations to 2 operations.\n"
            "Created new squashed migration %s\n"
            "  You should commit this migration but leave the old ones in place;\n"
            "  the new migration will be used for new installs. Once you are sure\n"
            "  all instances of the codebase have applied the migrations you "
            "squashed,\n"
            "  you can delete them.\n" % squashed_migration_file,
        )