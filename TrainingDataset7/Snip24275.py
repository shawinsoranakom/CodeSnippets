def test_equals_lookups(self):
        "Testing the 'same_as' and 'equals' lookup types."
        pnt = fromstr("POINT (-95.363151 29.763374)", srid=4326)
        c1 = City.objects.get(point=pnt)
        c2 = City.objects.get(point__same_as=pnt)
        c3 = City.objects.get(point__equals=pnt)
        for c in [c1, c2, c3]:
            self.assertEqual("Houston", c.name)