def apply(self, project_state, schema_editor, collect_sql=False):
                schema_editor.deferred_sql.append(DeferredSQL())