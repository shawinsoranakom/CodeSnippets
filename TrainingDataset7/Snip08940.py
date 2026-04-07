def __getitem__(self, index):
        if not isinstance(index, (int, slice)):
            raise TypeError(
                "AsyncPage indices must be integers or slices, not %s."
                % type(index).__name__
            )

        if not isinstance(self.object_list, list):
            raise TypeError(
                "AsyncPage.aget_object_list() must be awaited before using indexing."
            )
        return self.object_list[index]