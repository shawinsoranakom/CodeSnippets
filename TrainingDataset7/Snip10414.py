def ask_rename(self, model_name, old_name, new_name, field_instance):
        """Was this field really renamed?"""
        return self.defaults.get("ask_rename", False)