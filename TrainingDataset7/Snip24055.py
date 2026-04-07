def test_empty(self):
        self.assertIs(OGRGeometry("POINT (0 0)").empty, False)
        self.assertIs(OGRGeometry("POINT EMPTY").empty, True)