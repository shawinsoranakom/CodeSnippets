def _set_point_2d(self, index, value):
        x, y = value
        self._set_x(index, x)
        self._set_y(index, y)