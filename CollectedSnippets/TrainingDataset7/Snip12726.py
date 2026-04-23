def as_data(self):
        return ValidationError(self.data).error_list