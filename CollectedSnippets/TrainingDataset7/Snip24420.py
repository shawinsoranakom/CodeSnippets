def test00_GEOSIndexException(self):
        "Testing Geometry IndexError"
        p = Point(1, 2)
        for i in range(-2, 2):
            with self.subTest(i=i):
                p._checkindex(i)

        for i in (2, -3):
            with (
                self.subTest(i=i),
                self.assertRaisesMessage(IndexError, f"invalid index: {i}"),
            ):
                p._checkindex(i)