def format_value(self, value):
        return formats.localize_input(
            value, self.format or formats.get_format(self.format_key)[0]
        )