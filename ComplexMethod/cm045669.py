def _get_flatten_column_dtype(self):
        dtype = self.flatten_column.dtype
        if isinstance(dtype, dt.List):
            return dtype.wrapped
        if isinstance(dtype, dt.Tuple):
            if dtype in (dt.ANY_TUPLE, dt.Tuple()):
                return dt.ANY
            assert not isinstance(dtype.args, EllipsisType)
            return_dtype = dtype.args[0]
            for single_dtype in dtype.args[1:]:
                return_dtype = dt.types_lca(return_dtype, single_dtype, raising=False)
            return return_dtype
        elif dtype == dt.STR:
            return dt.STR
        elif dtype == dt.ANY:
            return dt.ANY
        elif isinstance(dtype, dt.Array):
            return dtype.strip_dimension()
        elif dtype == dt.JSON:
            return dt.JSON
        else:
            raise TypeError(f"Cannot flatten column of type {dtype}.")