def prepare_value(self, value):
        if hasattr(value, "_meta"):
            if self.to_field_name:
                return value.serializable_value(self.to_field_name)
            else:
                return value.pk
        return super().prepare_value(value)