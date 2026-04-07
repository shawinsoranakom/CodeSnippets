def test_contains(self):
        houston = City.objects.get(name="Houston")
        wellington = City.objects.get(name="Wellington")
        pueblo = City.objects.get(name="Pueblo")
        okcity = City.objects.get(name="Oklahoma City")
        lawrence = City.objects.get(name="Lawrence")

        # Now testing contains on the countries using the points for
        #  Houston and Wellington.
        tx = Country.objects.get(mpoly__contains=houston.point)  # Query w/GEOSGeometry
        nz = Country.objects.get(
            mpoly__contains=wellington.point.hex
        )  # Query w/EWKBHEX
        self.assertEqual("Texas", tx.name)
        self.assertEqual("New Zealand", nz.name)

        # Testing `contains` on the states using the point for Lawrence.
        ks = State.objects.get(poly__contains=lawrence.point)
        self.assertEqual("Kansas", ks.name)

        # Pueblo and Oklahoma City (even though OK City is within the bounding
        # box of Texas) are not contained in Texas or New Zealand.
        self.assertEqual(
            len(Country.objects.filter(mpoly__contains=pueblo.point)), 0
        )  # Query w/GEOSGeometry object
        self.assertEqual(
            len(Country.objects.filter(mpoly__contains=okcity.point.wkt)), 0
        )