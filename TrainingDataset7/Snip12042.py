def resolve_model_init_order(self):
        """Resolve the init field names and value positions."""
        converter = connections[self.db].introspection.identifier_converter
        model_init_fields = [
            field
            for column_name, field in self.model_fields.items()
            if column_name in self.columns
        ]
        annotation_fields = [
            (column, pos)
            for pos, column in enumerate(self.columns)
            if column not in self.model_fields
        ]
        model_init_order = [
            self.columns.index(converter(f.column)) for f in model_init_fields
        ]
        model_init_names = [f.attname for f in model_init_fields]
        return model_init_names, model_init_order, annotation_fields