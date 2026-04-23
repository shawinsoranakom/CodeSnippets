def test_access_band_data_directly_from_queryset(self):
        RasterModel.objects.create(rast=JSON_RASTER)
        qs = RasterModel.objects.all()
        qs[0].rast.bands[0].data()