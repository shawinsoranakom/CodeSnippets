def test03_PointApi(self):
        "Testing Point API"
        q = Point(4, 5, 3)
        for p in (Point(1, 2, 3), fromstr("POINT (1 2 3)")):
            p[0:2] = [4, 5]
            for f in geos_function_tests:
                with self.subTest(p=p, f=f):
                    self.assertEqual(f(q), f(p), "Point " + f.__name__)