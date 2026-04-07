def generate_removed_fields(self):
        """Make RemoveField operations."""
        for app_label, model_name, field_name in sorted(
            self.old_field_keys - self.new_field_keys
        ):
            self._generate_removed_field(app_label, model_name, field_name)