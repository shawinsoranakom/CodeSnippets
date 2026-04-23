def test_unionagg_tolerance(self):
        City.objects.create(
            point=fromstr("POINT(-96.467222 32.751389)", srid=4326),
            name="Forney",
        )
        tx = Country.objects.get(name="Texas").mpoly
        # Tolerance is greater than distance between Forney and Dallas, that's
        # why Dallas is ignored.
        forney_houston = GEOSGeometry(
            "MULTIPOINT(-95.363151 29.763374, -96.467222 32.751389)",
            srid=4326,
        )
        self.assertIs(
            forney_houston.equals_exact(
                City.objects.filter(point__within=tx).aggregate(
                    Union("point", tolerance=32000),
                )["point__union"],
                tolerance=10e-6,
            ),
            True,
        )