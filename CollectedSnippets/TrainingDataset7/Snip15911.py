def changed_data(self):
        data = super().changed_data
        if data:
            # Add arbitrary name to changed_data to test
            # change message construction.
            return data + ["not_a_form_field"]
        return data