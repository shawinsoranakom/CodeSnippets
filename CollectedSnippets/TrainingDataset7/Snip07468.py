def precision(self, precision):
        if (not isinstance(precision, int) or precision < 0) and precision is not None:
            raise AttributeError(
                "WKT output rounding precision must be non-negative integer or None."
            )
        if precision != self._precision:
            self._precision = precision
            wkt_writer_set_precision(self.ptr, -1 if precision is None else precision)