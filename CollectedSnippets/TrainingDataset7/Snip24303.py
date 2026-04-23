def test_geography_area(self):
        """
        Testing that Area calculations work on geography columns.
        """
        # SELECT ST_Area(poly) FROM geogapp_zipcode WHERE code='77002';
        z = Zipcode.objects.annotate(area=Area("poly")).get(code="77002")
        # Round to the nearest thousand as possible values (depending on
        # the database and geolib) include 5439084, 5439100, 5439101.
        rounded_value = z.area.sq_m
        rounded_value -= z.area.sq_m % 1000
        self.assertEqual(rounded_value, 5439000)