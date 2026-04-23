def get_by_natural_key(self, name, optional_id):
        return self.get(name=name, optional_id=optional_id)