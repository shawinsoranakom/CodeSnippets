def is_counterclockwise(self):
        if self.empty:
            raise ValueError("Orientation of an empty LinearRing cannot be determined.")
        return self._cs.is_counterclockwise