def flatchoices(self):
        """Flattened version of choices tuple."""
        return list(flatten_choices(self.choices))