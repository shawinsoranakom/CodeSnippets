def test_line_locate_point(self):
        pos_expr = functions.LineLocatePoint(
            LineString((0, 0), (0, 3), srid=4326), Point(0, 1, srid=4326)
        )
        self.assertAlmostEqual(
            State.objects.annotate(pos=pos_expr).first().pos, 0.3333333
        )