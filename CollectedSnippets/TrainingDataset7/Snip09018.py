def _handle_m2m_field_node(self, field, field_value):
        return base.deserialize_m2m_values(
            field, field_value, self.using, self.handle_forward_references
        )