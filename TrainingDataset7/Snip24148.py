def test_extent3d_filter(self):
        self._load_city_data()
        extent3d = City3D.objects.aggregate(
            ll_cities=Extent3D("point", filter=Q(name__contains="ll"))
        )["ll_cities"]
        ref_extent3d = (-96.801611, -41.315268, 14.0, 174.783117, 32.782057, 147.0)
        for ref_val, ext_val in zip(ref_extent3d, extent3d):
            self.assertAlmostEqual(ref_val, ext_val, 6)