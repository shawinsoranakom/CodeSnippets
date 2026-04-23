def __getitem__(self, index):
        """
        Get the Field object at the specified index, which may be either
        an integer or the Field's string label. Note that the Field object
        is not the field's _value_ -- use the `get` method instead to
        retrieve the value (e.g. an integer) instead of a Field instance.
        """
        if isinstance(index, str):
            i = self.index(index)
        elif 0 <= index < self.num_fields:
            i = index
        else:
            raise IndexError(
                "Index out of range when accessing field in a feature: %s." % index
            )
        return Field(self, i)