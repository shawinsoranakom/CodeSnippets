def range_params(self):
        params = self.params.copy()
        params.pop("q", None)
        return params