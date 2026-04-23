def value_from_datadict(self, data, files, name):
        value = data.get(name)
        return {
            True: True,
            "True": True,
            "False": False,
            False: False,
            "true": True,
            "false": False,
            # For backwards compatibility with Django < 2.2.
            "2": True,
            "3": False,
        }.get(value)