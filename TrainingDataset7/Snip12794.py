def format_value(self, value):
        """Only return the 'value' attribute if value isn't empty."""
        if value is True or value is False or value is None or value == "":
            return
        return str(value)