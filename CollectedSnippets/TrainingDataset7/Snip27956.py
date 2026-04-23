def backend_range(self):
        field = self.model._meta.get_field("value")
        internal_type = field.get_internal_type()
        return connection.ops.integer_field_range(internal_type)