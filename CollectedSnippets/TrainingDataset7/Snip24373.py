def test_threed(self):
        "Testing three-dimensional geometries."
        # Testing a 3D Point
        pnt = Point(2, 3, 8)
        self.assertEqual((2.0, 3.0, 8.0), pnt.coords)
        msg = "Dimension of value does not match."
        with self.assertRaisesMessage(TypeError, msg):
            pnt.tuple = (1.0, 2.0)
        pnt.coords = (1.0, 2.0, 3.0)
        self.assertEqual((1.0, 2.0, 3.0), pnt.coords)

        # Testing a 3D LineString
        ls = LineString((2.0, 3.0, 8.0), (50.0, 250.0, -117.0))
        self.assertEqual(((2.0, 3.0, 8.0), (50.0, 250.0, -117.0)), ls.tuple)
        with self.assertRaisesMessage(TypeError, msg):
            ls.__setitem__(0, (1.0, 2.0))
        ls[0] = (1.0, 2.0, 3.0)
        self.assertEqual((1.0, 2.0, 3.0), ls[0])