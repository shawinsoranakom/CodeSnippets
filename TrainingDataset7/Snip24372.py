def test_geometry_collection_list_assignment(self):
        p = Point()
        gc = GeometryCollection()

        gc[:] = [p]
        self.assertEqual(gc, GeometryCollection(p))

        gc[:] = ()
        self.assertEqual(gc, GeometryCollection())