def _fixture_setup(cls):
        for db_name in cls._databases_names(include_mirrors=False):
            # Reset sequences
            if cls.reset_sequences:
                cls._reset_sequences(db_name)

            # Provide replica initial data from migrated apps, if needed.
            if cls.serialized_rollback and hasattr(
                connections[db_name], "_test_serialized_contents"
            ):
                if cls.available_apps is not None:
                    apps.unset_available_apps()
                connections[db_name].creation.deserialize_db_from_string(
                    connections[db_name]._test_serialized_contents
                )
                if cls.available_apps is not None:
                    apps.set_available_apps(cls.available_apps)

            if cls.fixtures:
                call_command("loaddata", *cls.fixtures, verbosity=0, database=db_name)