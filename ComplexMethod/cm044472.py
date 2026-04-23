def _convert_dtype(cls, data_type: T.Any, val: T.Any) -> DataclassDict | np.ndarray | None:
        """Convert a serialized dict to a DataclassDict or list to a numpy array of the correct
        dtype

        Parameters
        ----------
        field_type
            The field type for the incoming value
        value
            The list to convert to a numpy array or DataclassDict

        Returns
        -------
        The inbound item to a DataclassDict or numpy array. ``None`` if the item does not convert
        """
        if isinstance(data_type, type) and issubclass(data_type, DataclassDict):
            return data_type.from_dict(val)

        origin = T.get_origin(data_type)
        if origin is types.UnionType:
            args = tuple(a for a in T.get_args(data_type) if a is not types.NoneType)
            assert len(args) == 1
            if val is None:
                return val
            data_type = args[0]
            origin = T.get_origin(data_type)

        if origin is not np.ndarray:
            return None

        args = T.get_args(data_type)
        dtype = T.get_args(args[1])[0]
        return np.array(val, dtype=dtype)