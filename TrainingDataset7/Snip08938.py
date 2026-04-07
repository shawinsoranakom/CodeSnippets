def __len__(self):
        if not isinstance(self.object_list, list):
            raise TypeError(
                "AsyncPage.aget_object_list() must be awaited before calling len()."
            )
        return len(self.object_list)