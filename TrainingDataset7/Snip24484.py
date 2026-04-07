def alter_gis_model(
        self,
        migration_class,
        model_name,
        field_name,
        field_class=None,
        field_class_kwargs=None,
    ):
        args = [model_name, field_name]
        if field_class:
            field_class_kwargs = field_class_kwargs or {}
            args.append(field_class(**field_class_kwargs))
        operation = migration_class(*args)
        old_state = self.current_state.clone()
        operation.state_forwards("gis", self.current_state)
        with connection.schema_editor() as editor:
            operation.database_forwards("gis", editor, old_state, self.current_state)