def _field_should_be_indexed(self, model, field):
        create_index = super()._field_should_be_indexed(model, field)
        db_type = field.db_type(self.connection)
        if (
            db_type is not None
            and db_type.lower() in self.connection._limited_data_types
        ):
            return False
        return create_index