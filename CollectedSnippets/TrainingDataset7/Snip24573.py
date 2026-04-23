def test07_values(self):
        "Testing values() and values_list()."
        gqs = Location.objects.all()
        gvqs = Location.objects.values()
        gvlqs = Location.objects.values_list()

        # Incrementing through each of the models, dictionaries, and tuples
        # returned by each QuerySet.
        for m, d, t in zip(gqs, gvqs, gvlqs):
            # The values should be Geometry objects and not raw strings
            # returned by the spatial database.
            self.assertIsInstance(d["point"], GEOSGeometry)
            self.assertIsInstance(t[1], GEOSGeometry)
            self.assertEqual(m.point, d["point"])
            self.assertEqual(m.point, t[1])