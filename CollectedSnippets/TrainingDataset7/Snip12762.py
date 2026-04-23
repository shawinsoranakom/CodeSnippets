def format_value(self, value):
        """
        Return a value as it should appear when rendered in a template.
        """
        if value == "" or value is None:
            return None
        if self.is_localized:
            return formats.localize_input(value)
        return str(value)