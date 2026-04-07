def has_error(self, field, code=None):
        return field in self.errors and (
            code is None
            or any(error.code == code for error in self.errors.as_data()[field])
        )