def database_forwards(self, app_label, schema_editor, from_state, to_state):
        """
        Perform the mutation on the database schema in the normal
        (forwards) direction.
        """
        raise NotImplementedError(
            "subclasses of Operation must provide a database_forwards() method"
        )