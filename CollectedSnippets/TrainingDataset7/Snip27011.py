def unapply_operations(self, app_label, project_state, operations, atomic=True):
        migration = Migration("name", app_label)
        migration.operations = operations
        with connection.schema_editor(atomic=atomic) as editor:
            return migration.unapply(project_state, editor)