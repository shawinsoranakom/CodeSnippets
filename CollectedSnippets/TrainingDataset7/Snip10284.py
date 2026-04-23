def references_model(self, name, app_label):
        return (
            name.lower() == self.old_name_lower or name.lower() == self.new_name_lower
        )