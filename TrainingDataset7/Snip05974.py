def value_from_datadict(self, data, files, name):
        value = data.get(name)
        if value:
            return value.split(",")