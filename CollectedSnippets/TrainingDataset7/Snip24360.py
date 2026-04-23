def test_buffer(self):
        bg = self.geometries.buffer_geoms[0]
        g = fromstr(bg.wkt)

        # Can't use a floating-point for the number of quadsegs.
        with self.assertArgumentTypeError(4, "float"):
            g.buffer(bg.width, quadsegs=1.1)

        self._test_buffer(self.geometries.buffer_geoms, "buffer")