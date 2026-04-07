def get_index_by_name(self, name):
        for index in self.options["indexes"]:
            if index.name == name:
                return index
        raise ValueError("No index named %s on model %s" % (name, self.name))