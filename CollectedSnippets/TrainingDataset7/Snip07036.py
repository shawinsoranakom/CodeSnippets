def __getitem__(self, index):
        "Get the Feature at the specified index."
        if isinstance(index, int):
            # An integer index was given -- we cannot do a check based on the
            # number of features because the beginning and ending feature IDs
            # are not guaranteed to be 0 and len(layer)-1, respectively.
            if index < 0:
                raise IndexError("Negative indices are not allowed on OGR Layers.")
            return self._make_feature(index)
        elif isinstance(index, slice):
            # A slice was given
            start, stop, stride = index.indices(self.num_feat)
            return [self._make_feature(fid) for fid in range(start, stop, stride)]
        else:
            raise TypeError(
                "Integers and slices may only be used when indexing OGR Layers."
            )