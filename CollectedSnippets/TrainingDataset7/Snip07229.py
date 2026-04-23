def _set_point_3d_m(self, index, value):
        x, y, m = value
        self._set_x(index, x)
        self._set_y(index, y)
        self._set_m(index, m)