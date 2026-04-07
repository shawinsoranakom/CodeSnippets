def test06_f_expressions(self):
        "Testing F() expressions on GeometryFields."
        # Constructing a dummy parcel border and getting the City instance for
        # assigning the FK.
        b1 = GEOSGeometry(
            "POLYGON((-97.501205 33.052520,-97.501205 33.052576,"
            "-97.501150 33.052576,-97.501150 33.052520,-97.501205 33.052520))",
            srid=4326,
        )
        pcity = City.objects.get(name="Aurora")

        # First parcel has incorrect center point that is equal to the City;
        # it also has a second border that is different from the first as a
        # 100ft buffer around the City.
        c1 = pcity.location.point
        c2 = c1.transform(2276, clone=True)
        b2 = c2.buffer(100)
        Parcel.objects.create(
            name="P1", city=pcity, center1=c1, center2=c2, border1=b1, border2=b2
        )

        # Now creating a second Parcel where the borders are the same, just
        # in different coordinate systems. The center points are also the
        # same (but in different coordinate systems), and this time they
        # actually correspond to the centroid of the border.
        c1 = b1.centroid
        c2 = c1.transform(2276, clone=True)
        b2 = (
            b1
            if connection.features.supports_transform
            else b1.transform(2276, clone=True)
        )
        Parcel.objects.create(
            name="P2", city=pcity, center1=c1, center2=c2, border1=b1, border2=b2
        )

        # Should return the second Parcel, which has the center within the
        # border.
        qs = Parcel.objects.filter(center1__within=F("border1"))
        self.assertEqual(1, len(qs))
        self.assertEqual("P2", qs[0].name)

        # This time center2 is in a different coordinate system and needs to be
        # wrapped in transformation SQL.
        qs = Parcel.objects.filter(center2__within=F("border1"))
        if connection.features.supports_transform:
            self.assertEqual("P2", qs.get().name)
        else:
            msg = "This backend doesn't support the Transform function."
            with self.assertRaisesMessage(NotSupportedError, msg):
                list(qs)

        # Should return the first Parcel, which has the center point equal
        # to the point in the City ForeignKey.
        qs = Parcel.objects.filter(center1=F("city__location__point"))
        self.assertEqual(1, len(qs))
        self.assertEqual("P1", qs[0].name)

        # This time the city column should be wrapped in transformation SQL.
        qs = Parcel.objects.filter(border2__contains=F("city__location__point"))
        if connection.features.supports_transform:
            self.assertEqual("P1", qs.get().name)
        else:
            msg = "This backend doesn't support the Transform function."
            with self.assertRaisesMessage(NotSupportedError, msg):
                list(qs)