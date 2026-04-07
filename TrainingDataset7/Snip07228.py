def _set_point_3d(self, index, value):
        x, y, z = value
        self._set_x(index, x)
        self._set_y(index, y)
        self._set_z(index, z)