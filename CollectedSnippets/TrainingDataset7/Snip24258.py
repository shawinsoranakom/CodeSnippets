def test_inherited_geofields(self):
        "Database functions on inherited Geometry fields."
        # Creating a Pennsylvanian city.
        PennsylvaniaCity.objects.create(
            name="Mansfield", county="Tioga", point="POINT(-77.071445 41.823881)"
        )

        # All transformation SQL will need to be performed on the
        # _parent_ table.
        qs = PennsylvaniaCity.objects.annotate(
            new_point=functions.Transform("point", srid=32128)
        )

        self.assertEqual(1, qs.count())
        for pc in qs:
            self.assertEqual(32128, pc.new_point.srid)