def test_geodetic_area_raises_if_not_supported(self):
        with self.assertRaisesMessage(
            NotSupportedError, "Area on geodetic coordinate systems not supported."
        ):
            Zipcode.objects.annotate(area=Area("poly")).get(code="77002")