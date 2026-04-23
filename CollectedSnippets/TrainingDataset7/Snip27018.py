def test_migrate(self):
        """
        Tests basic usage of the migrate command.
        """
        # No tables are created
        self.assertTableNotExists("migrations_author")
        self.assertTableNotExists("migrations_tribble")
        self.assertTableNotExists("migrations_book")
        # Run the migrations to 0001 only
        stdout = io.StringIO()
        call_command(
            "migrate", "migrations", "0001", verbosity=2, stdout=stdout, no_color=True
        )
        stdout = stdout.getvalue()
        self.assertIn(
            "Target specific migration: 0001_initial, from migrations", stdout
        )
        self.assertIn("Applying migrations.0001_initial... OK", stdout)
        self.assertIn("Running pre-migrate handlers for application migrations", stdout)
        self.assertIn(
            "Running post-migrate handlers for application migrations", stdout
        )
        # The correct tables exist
        self.assertTableExists("migrations_author")
        self.assertTableExists("migrations_tribble")
        self.assertTableNotExists("migrations_book")
        # Run migrations all the way
        call_command("migrate", verbosity=0)
        # The correct tables exist
        self.assertTableExists("migrations_author")
        self.assertTableNotExists("migrations_tribble")
        self.assertTableExists("migrations_book")
        # Unmigrate everything
        stdout = io.StringIO()
        call_command(
            "migrate", "migrations", "zero", verbosity=2, stdout=stdout, no_color=True
        )
        stdout = stdout.getvalue()
        self.assertIn("Unapply all migrations: migrations", stdout)
        self.assertIn("Unapplying migrations.0002_second... OK", stdout)
        self.assertIn("Running pre-migrate handlers for application migrations", stdout)
        self.assertIn(
            "Running post-migrate handlers for application migrations", stdout
        )
        # Tables are gone
        self.assertTableNotExists("migrations_author")
        self.assertTableNotExists("migrations_tribble")
        self.assertTableNotExists("migrations_book")