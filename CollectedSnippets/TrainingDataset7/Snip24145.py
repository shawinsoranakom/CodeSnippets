def test_bulk_create_point_field(self):
        objs = Point2D.objects.bulk_create([Point2D(), Point2D()])
        self.assertEqual(len(objs), 2)