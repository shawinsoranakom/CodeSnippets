def _get_point_4d(self, index):
        return (
            self._get_x(index),
            self._get_y(index),
            self._get_z(index),
            self._get_m(index),
        )