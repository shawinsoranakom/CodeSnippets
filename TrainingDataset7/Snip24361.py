def test_buffer_with_style(self):
        bg = self.geometries.buffer_with_style_geoms[0]
        g = fromstr(bg.wkt)

        # Can't use a floating-point for the number of quadsegs.
        with self.assertArgumentTypeError(4, "float"):
            g.buffer_with_style(bg.width, quadsegs=1.1)

        # Can't use a floating-point for the end cap style.
        with self.assertArgumentTypeError(5, "float"):
            g.buffer_with_style(bg.width, end_cap_style=1.2)
        # Can't use a end cap style that is not in the enum.
        msg = self.error_checking_geom.format("GEOSBufferWithStyle_r")
        with self.assertRaisesMessage(GEOSException, msg):
            g.buffer_with_style(bg.width, end_cap_style=55)

        # Can't use a floating-point for the join style.
        with self.assertArgumentTypeError(6, "float"):
            g.buffer_with_style(bg.width, join_style=1.3)
        # Can't use a join style that is not in the enum.
        with self.assertRaisesMessage(GEOSException, msg):
            g.buffer_with_style(bg.width, join_style=66)

        self._test_buffer(
            itertools.chain(
                self.geometries.buffer_geoms, self.geometries.buffer_with_style_geoms
            ),
            "buffer_with_style",
        )