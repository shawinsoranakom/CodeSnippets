def _point_getter(self):
        if self.dims == 3 and self._z:
            return self._get_point_3d
        elif self.dims == 3 and self.hasm:
            return self._get_point_3d_m
        elif self.dims == 4 and self._z and self.hasm:
            return self._get_point_4d
        return self._get_point_2d