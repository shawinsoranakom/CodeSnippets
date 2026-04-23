def get_prep_value(self, value):
        value = super().get_prep_value(value)
        # Need to convert File objects provided via a form to string for
        # database insertion.
        if value is None:
            return None
        return str(value)