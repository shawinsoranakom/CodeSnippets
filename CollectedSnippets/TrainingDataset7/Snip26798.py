def assertOperationFieldAttributes(
        self, changes, app_label, position, operation_position, **attrs
    ):
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
        if len(changes[app_label]) < position + 1:
            self.fail(
                "No operation at index %s for %s.%s\n%s"
                % (
                    operation_position,
                    app_label,
                    migration.name,
                    self.repr_changes(changes),
                )
            )
        operation = migration.operations[operation_position]
        if not hasattr(operation, "field"):
            self.fail(
                "No field attribute for %s.%s op #%s."
                % (
                    app_label,
                    migration.name,
                    operation_position,
                )
            )
        field = operation.field
        for attr, value in attrs.items():
            if getattr(field, attr, None) != value:
                self.fail(
                    "Field attribute mismatch for %s.%s op #%s, field.%s (expected %r, "
                    "got %r):\n%s"
                    % (
                        app_label,
                        migration.name,
                        operation_position,
                        attr,
                        value,
                        getattr(field, attr, None),
                        self.repr_changes(changes),
                    )
                )