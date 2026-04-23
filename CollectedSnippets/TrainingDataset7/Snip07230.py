def _set_point_4d(self, index, value):
        x, y, z, m = value
        self._set_x(index, x)
        self._set_y(index, y)
        self._set_z(index, z)
        self._set_m(index, m)