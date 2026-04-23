def assertOperationTypes(self, changes, app_label, position, types):
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
        real_types = [
            operation.__class__.__name__ for operation in migration.operations
        ]
        if types != real_types:
            self.fail(
                "Operation type mismatch for %s.%s (expected %s):\n%s"
                % (
                    app_label,
                    migration.name,
                    types,
                    self.repr_changes(changes),
                )
            )