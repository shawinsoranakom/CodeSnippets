def references_model(self, name, app_label):
        # The deleted model could be referencing the specified model through
        # related fields.
        return True