def __reversed__(self):
        if not isinstance(self.object_list, list):
            raise TypeError(
                "AsyncPage.aget_object_list() "
                "must be awaited before calling reversed()."
            )

        return reversed(self.object_list)