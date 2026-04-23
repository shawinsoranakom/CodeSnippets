def get_transform(self, name):
        transform = super().get_transform(name)
        if transform:
            return transform
        if "_" not in name:
            try:
                index = int(name)
            except ValueError:
                pass
            else:
                index += 1  # postgres uses 1-indexing
                return IndexTransformFactory(index, self.base_field)
        try:
            start, end = name.split("_")
            start = int(start) + 1
            end = int(end)  # don't add one here because postgres slices are weird
        except ValueError:
            pass
        else:
            return SliceTransformFactory(start, end)