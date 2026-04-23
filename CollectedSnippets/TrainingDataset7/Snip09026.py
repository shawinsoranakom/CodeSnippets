def represent_ordered_dict(self, data):
        return self.represent_mapping("tag:yaml.org,2002:map", data.items())