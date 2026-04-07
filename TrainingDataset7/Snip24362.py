def _test_buffer(self, geometries, buffer_method_name):
        for bg in geometries:
            g = fromstr(bg.wkt)

            # The buffer we expect
            exp_buf = fromstr(bg.buffer_wkt)

            # Constructing our buffer
            buf_kwargs = {
                kwarg_name: getattr(bg, kwarg_name)
                for kwarg_name in (
                    "width",
                    "quadsegs",
                    "end_cap_style",
                    "join_style",
                    "mitre_limit",
                )
                if hasattr(bg, kwarg_name)
            }
            buf = getattr(g, buffer_method_name)(**buf_kwargs)
            with self.subTest(bg=bg):
                self.assertEqual(exp_buf.num_coords, buf.num_coords)
                self.assertEqual(len(exp_buf), len(buf))

                # Now assuring that each point in the buffer is almost equal
                for exp_ring, buf_ring in zip(exp_buf, buf, strict=True):
                    for exp_point, buf_point in zip(exp_ring, buf_ring, strict=True):
                        # Asserting the X, Y of each point are almost equal
                        # (due to floating point imprecision).
                        self.assertAlmostEqual(exp_point[0], buf_point[0], 9)
                        self.assertAlmostEqual(exp_point[1], buf_point[1], 9)