def __setitem__(self, index, value):
        "Set the coordinate sequence value at the given index."
        # Checking the input value
        if isinstance(value, (list, tuple)):
            pass
        elif numpy and isinstance(value, numpy.ndarray):
            pass
        else:
            raise TypeError(
                "Must set coordinate with a sequence (list, tuple, or numpy array)."
            )
        # Checking the dims of the input
        if self.dims == 3 and self._z:
            n_args = 3
            point_setter = self._set_point_3d
        elif self.dims == 3 and self.hasm:
            n_args = 3
            point_setter = self._set_point_3d_m
        elif self.dims == 4 and self._z and self.hasm:
            n_args = 4
            point_setter = self._set_point_4d
        else:
            n_args = 2
            point_setter = self._set_point_2d
        if len(value) != n_args:
            raise TypeError("Dimension of value does not match.")
        self._checkindex(index)
        point_setter(index, value)