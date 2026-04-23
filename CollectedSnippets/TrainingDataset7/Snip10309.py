def references_field(self, model_name, name, app_label):
        return self.references_model(model_name, app_label) and (
            not self.option_value
            or any((name in fields) for fields in self.option_value)
        )