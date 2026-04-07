def test_perimeter_geodetic(self):
        # Currently only Oracle supports calculating the perimeter on geodetic
        # geometries (without being transformed).
        qs1 = CensusZipcode.objects.annotate(perim=Perimeter("poly"))
        if connection.features.supports_perimeter_geodetic:
            self.assertAlmostEqual(qs1[0].perim.m, 18406.3818954314, 3)
        else:
            with self.assertRaises(NotSupportedError):
                list(qs1)
        # But should work fine when transformed to projected coordinates
        qs2 = CensusZipcode.objects.annotate(
            perim=Perimeter(Transform("poly", 32140))
        ).filter(name="77002")
        self.assertAlmostEqual(qs2[0].perim.m, 18404.355, 3)