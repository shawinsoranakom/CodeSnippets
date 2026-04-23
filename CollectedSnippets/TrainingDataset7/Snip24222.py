def test_sym_difference(self):
        geom = Point(5, 23, srid=4326)
        qs = Country.objects.annotate(
            sym_difference=functions.SymDifference("mpoly", geom)
        )
        # Oracle does something screwy with the Texas geometry.
        if connection.ops.oracle:
            qs = qs.exclude(name="Texas")
        for country in qs:
            self.assertTrue(
                country.mpoly.sym_difference(geom).equals(country.sym_difference)
            )