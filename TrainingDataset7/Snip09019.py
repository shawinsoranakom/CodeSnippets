def _handle_fk_field_node(self, field, field_value):
        return base.deserialize_fk_value(
            field, field_value, self.using, self.handle_forward_references
        )