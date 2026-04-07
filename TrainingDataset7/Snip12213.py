def __str__(self):
        if self.params_type is None:
            return self.sql
        return self.sql % self.params_type(self.params)