def test_first_dependency(self):
        """
        A dependency to an app with no migrations uses __first__.
        """
        # Load graph
        loader = MigrationLoader(connection)
        before = self.make_project_state([])
        after = self.make_project_state([self.book_migrations_fk])
        after.real_apps = {"migrations"}
        autodetector = MigrationAutodetector(before, after)
        changes = autodetector._detect_changes(graph=loader.graph)
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "otherapp", 1)
        self.assertOperationTypes(changes, "otherapp", 0, ["CreateModel"])
        self.assertOperationAttributes(changes, "otherapp", 0, 0, name="Book")
        self.assertMigrationDependencies(
            changes, "otherapp", 0, [("migrations", "__first__")]
        )