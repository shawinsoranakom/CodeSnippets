def test_contained(self):
        # Getting Texas, yes we were a country -- once ;)
        texas = Country.objects.get(name="Texas")

        # Seeing what cities are in Texas, should get Houston and Dallas,
        #  and Oklahoma City because 'contained' only checks on the
        #  _bounding box_ of the Geometries.
        qs = City.objects.filter(point__contained=texas.mpoly)
        self.assertEqual(3, qs.count())
        cities = ["Houston", "Dallas", "Oklahoma City"]
        for c in qs:
            self.assertIn(c.name, cities)