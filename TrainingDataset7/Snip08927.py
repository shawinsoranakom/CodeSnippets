def __getitem__(self, index):
        if not isinstance(index, (int, slice)):
            raise TypeError(
                "Page indices must be integers or slices, not %s."
                % type(index).__name__
            )
        # The object_list is converted to a list so that if it was a QuerySet
        # it won't be a database hit per __getitem__.
        if not isinstance(self.object_list, list):
            self.object_list = list(self.object_list)
        return self.object_list[index]