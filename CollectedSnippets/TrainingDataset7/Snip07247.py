def tuple(self):
        "Return a tuple version of this coordinate sequence."
        n = self.size
        get_point = self._point_getter
        if n == 1:
            return get_point(0)
        return tuple(get_point(i) for i in range(n))