def params_type(self):
        if self.params is None:
            return None
        return dict if isinstance(self.params, Mapping) else tuple