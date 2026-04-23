def _fixture_teardown(self):
        # Allow TRUNCATE ... CASCADE and don't emit the post_migrate signal
        # when flushing only a subset of the apps
        for db_name in self._databases_names(include_mirrors=False):
            # Flush the database
            inhibit_post_migrate = (
                self.available_apps is not None
                or (  # Inhibit the post_migrate signal when using serialized
                    # rollback to avoid trying to recreate the serialized data.
                    self.serialized_rollback
                    and hasattr(connections[db_name], "_test_serialized_contents")
                )
            )
            call_command(
                "flush",
                verbosity=0,
                interactive=False,
                database=db_name,
                reset_sequences=False,
                allow_cascade=self.available_apps is not None,
                inhibit_post_migrate=inhibit_post_migrate,
            )