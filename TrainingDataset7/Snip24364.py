def test_closed(self):
        ls_closed = LineString((0, 0), (1, 1), (0, 0))
        ls_not_closed = LineString((0, 0), (1, 1))
        self.assertFalse(ls_not_closed.closed)
        self.assertTrue(ls_closed.closed)