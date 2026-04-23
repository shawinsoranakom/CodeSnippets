def test_deserialize_with_pixeltype_flags(self):
        no_data = 3
        rast = GDALRaster(
            {
                "srid": 4326,
                "origin": [0, 0],
                "scale": [-1, 1],
                "skew": [0, 0],
                "width": 1,
                "height": 1,
                "nr_of_bands": 1,
                "bands": [{"data": [no_data], "nodata_value": no_data}],
            }
        )
        r = RasterModel.objects.create(rast=rast)
        RasterModel.objects.filter(pk=r.pk).update(
            rast=Func(F("rast"), function="ST_SetBandIsNoData"),
        )
        r.refresh_from_db()
        band = r.rast.bands[0].data()
        if numpy:
            band = band.flatten().tolist()
        self.assertEqual(band, [no_data])
        self.assertEqual(r.rast.bands[0].nodata_value, no_data)