def format_value(self, value):
        try:
            return {
                True: "true",
                False: "false",
                "true": "true",
                "false": "false",
                # For backwards compatibility with Django < 2.2.
                "2": "true",
                "3": "false",
            }[value]
        except KeyError:
            return "unknown"