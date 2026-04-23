def database_forwards(self, app_label, schema_editor, from_state, to_state):
        # RunPython has access to all models. Ensure that all models are
        # reloaded in case any are delayed.
        from_state.clear_delayed_apps_cache()
        if router.allow_migrate(
            schema_editor.connection.alias, app_label, **self.hints
        ):
            # We now execute the Python code in a context that contains a
            # 'models' object, representing the versioned models as an app
            # registry. We could try to override the global cache, but then
            # people will still use direct imports, so we go with a
            # documentation approach instead.
            self.code(from_state.apps, schema_editor)