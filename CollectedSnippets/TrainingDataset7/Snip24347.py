def test_polygons_from_bbox(self):
        "Testing `from_bbox` class method."
        bbox = (-180, -90, 180, 90)
        p = Polygon.from_bbox(bbox)
        self.assertEqual(bbox, p.extent)

        # Testing numerical precision
        x = 3.14159265358979323
        bbox = (0, 0, 1, x)
        p = Polygon.from_bbox(bbox)
        y = p.extent[-1]
        self.assertEqual(format(x, ".13f"), format(y, ".13f"))