def assertMigrationDependencies(self, changes, app_label, position, dependencies):
        if not changes.get(app_label):
            self.fail(
                "No migrations found for %s\n%s"
                % (app_label, self.repr_changes(changes))
            )
        if len(changes[app_label]) < position + 1:
            self.fail(
                "No migration at index %s for %s\n%s"
                % (position, app_label, self.repr_changes(changes))
            )
        migration = changes[app_label][position]
        if set(migration.dependencies) != set(dependencies):
            self.fail(
                "Migration dependencies mismatch for %s.%s (expected %s):\n%s"
                % (
                    app_label,
                    migration.name,
                    dependencies,
                    self.repr_changes(changes, include_dependencies=True),
                )
            )