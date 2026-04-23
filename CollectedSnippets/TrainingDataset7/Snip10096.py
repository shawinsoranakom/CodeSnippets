def generate_added_fields(self):
        """Make AddField operations."""
        for app_label, model_name, field_name in sorted(
            self.new_field_keys - self.old_field_keys
        ):
            self._generate_added_field(app_label, model_name, field_name)