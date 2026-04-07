def test_squashmigrations_manual_porting(self):
        out = io.StringIO()
        with self.temporary_migration_module(
            module="migrations.test_migrations_manual_porting",
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
                migration_dir,
                "0001_squashed_0002_second.py",
            )
            self.assertTrue(os.path.exists(squashed_migration_file))
        black_warning = ""
        if HAS_BLACK:
            black_warning = (
                "Squashed migration couldn't be formatted using the "
                '"black" command. You can call it manually.\n'
            )
        self.assertEqual(
            out.getvalue(),
            f"Will squash the following migrations:\n"
            f" - 0001_initial\n"
            f" - 0002_second\n"
            f"Optimizing...\n"
            f"  No optimizations possible.\n"
            f"Created new squashed migration {squashed_migration_file}\n"
            f"  You should commit this migration but leave the old ones in place;\n"
            f"  the new migration will be used for new installs. Once you are sure\n"
            f"  all instances of the codebase have applied the migrations you "
            f"squashed,\n"
            f"  you can delete them.\n"
            f"Manual porting required\n"
            f"  Your migrations contained functions that must be manually copied "
            f"over,\n"
            f"  as we could not safely copy their implementation.\n"
            f"  See the comment at the top of the squashed migration for details.\n"
            + black_warning,
        )