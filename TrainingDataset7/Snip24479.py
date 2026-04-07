def apply_operations(self, app_label, project_state, operations):
        migration = Migration("name", app_label)
        migration.operations = operations
        with connection.schema_editor() as editor:
            return migration.apply(project_state, editor)