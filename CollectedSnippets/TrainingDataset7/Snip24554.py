def test_lookup_invalid_band_lhs(self):
        """
        Typical left-hand side usage is protected against non-integers, but for
        defense-in-depth purposes, construct custom lookups that evade the
        `int()` and `+ 1` checks in the lookups shipped by django.contrib.gis.
        """

        # Evade the int() call in RasterField.get_transform().
        class MyRasterBandTransform(RasterBandTransform):
            band_index = "evil"

            def process_band_indices(self, *args, **kwargs):
                self.band_lhs = self.lhs.band_index
                self.band_rhs, *self.rhs_params = self.rhs_params

        # Evade the `+ 1` call in BaseSpatialField.process_band_indices().
        ContainsLookup = RasterModel._meta.get_field("rast").get_lookup("contains")

        class MyContainsLookup(ContainsLookup):
            def process_band_indices(self, *args, **kwargs):
                self.band_lhs = self.lhs.band_index
                self.band_rhs, *self.rhs_params = self.rhs_params

        RasterField = RasterModel._meta.get_field("rast")
        RasterField.register_lookup(MyContainsLookup, "contains")
        self.addCleanup(RasterField.register_lookup, ContainsLookup, "contains")

        qs = RasterModel.objects.annotate(
            transformed=MyRasterBandTransform("rast")
        ).filter(transformed__contains=(F("transformed"), 1))
        msg = "Band index must be an integer, but got 'str'."
        with self.assertRaisesMessage(TypeError, msg):
            list(qs)