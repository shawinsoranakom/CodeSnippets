def test_migrate_fake_initial(self):
        """
        --fake-initial only works if all tables created in the initial
        migration of an app exists. Database routers must be obeyed when doing
        that check.
        """
        # Make sure no tables are created
        for db in self.databases:
            self.assertTableNotExists("migrations_author", using=db)
            self.assertTableNotExists("migrations_tribble", using=db)

        try:
            # Run the migrations to 0001 only
            call_command("migrate", "migrations", "0001", verbosity=0)
            call_command("migrate", "migrations", "0001", verbosity=0, database="other")
            # Make sure the right tables exist
            self.assertTableExists("migrations_author")
            self.assertTableNotExists("migrations_tribble")
            # Also check the "other" database
            self.assertTableNotExists("migrations_author", using="other")
            self.assertTableExists("migrations_tribble", using="other")
            # Fake a roll-back
            call_command("migrate", "migrations", "zero", fake=True, verbosity=0)
            call_command(
                "migrate",
                "migrations",
                "zero",
                fake=True,
                verbosity=0,
                database="other",
            )
            # Make sure the tables still exist
            self.assertTableExists("migrations_author")
            self.assertTableExists("migrations_tribble", using="other")
            # Try to run initial migration
            with self.assertRaises(DatabaseError):
                call_command("migrate", "migrations", "0001", verbosity=0)
            # Run initial migration with an explicit --fake-initial
            out = io.StringIO()
            with mock.patch(
                "django.core.management.color.supports_color", lambda *args: False
            ):
                call_command(
                    "migrate",
                    "migrations",
                    "0001",
                    fake_initial=True,
                    stdout=out,
                    verbosity=1,
                )
                call_command(
                    "migrate",
                    "migrations",
                    "0001",
                    fake_initial=True,
                    verbosity=0,
                    database="other",
                )
            self.assertIn("migrations.0001_initial... faked", out.getvalue().lower())

            # Run migrations all the way.
            call_command("migrate", verbosity=0)
            call_command("migrate", verbosity=0, database="other")
            self.assertTableExists("migrations_author")
            self.assertTableNotExists("migrations_tribble")
            self.assertTableExists("migrations_book")
            self.assertTableNotExists("migrations_author", using="other")
            self.assertTableNotExists("migrations_tribble", using="other")
            self.assertTableNotExists("migrations_book", using="other")
            # Fake a roll-back.
            call_command("migrate", "migrations", "zero", fake=True, verbosity=0)
            call_command(
                "migrate",
                "migrations",
                "zero",
                fake=True,
                verbosity=0,
                database="other",
            )
            self.assertTableExists("migrations_author")
            self.assertTableNotExists("migrations_tribble")
            self.assertTableExists("migrations_book")
            # Run initial migration.
            with self.assertRaises(DatabaseError):
                call_command("migrate", "migrations", verbosity=0)
            # Run initial migration with an explicit --fake-initial.
            with self.assertRaises(DatabaseError):
                # Fails because "migrations_tribble" does not exist but needs
                # to in order to make --fake-initial work.
                call_command("migrate", "migrations", fake_initial=True, verbosity=0)
            # Fake an apply.
            call_command("migrate", "migrations", fake=True, verbosity=0)
            call_command(
                "migrate", "migrations", fake=True, verbosity=0, database="other"
            )
        finally:
            # Unmigrate everything.
            call_command("migrate", "migrations", "zero", verbosity=0)
            call_command("migrate", "migrations", "zero", verbosity=0, database="other")
        # Make sure it's all gone
        for db in self.databases:
            self.assertTableNotExists("migrations_author", using=db)
            self.assertTableNotExists("migrations_tribble", using=db)
            self.assertTableNotExists("migrations_book", using=db)