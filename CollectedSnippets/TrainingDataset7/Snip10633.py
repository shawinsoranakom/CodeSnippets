def _assign_returned_values(self, returned_values, returning_fields):
        returning_fields_iter = iter(returning_fields)
        for value, field in zip(returned_values, returning_fields_iter):
            setattr(self, field.attname, value)
        # Defer all fields that were meant to be updated with their database
        # resolved values but couldn't as they are effectively stale.
        for field in returning_fields_iter:
            self.__dict__.pop(field.attname, None)