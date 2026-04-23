def setUp(self):
        rast = GDALRaster(
            {
                "srid": 4326,
                "origin": [0, 0],
                "scale": [-1, 1],
                "skew": [0, 0],
                "width": 5,
                "height": 5,
                "nr_of_bands": 2,
                "bands": [{"data": range(25)}, {"data": range(25, 50)}],
            }
        )
        model_instance = RasterModel.objects.create(
            rast=rast,
            rastprojected=rast,
            geom="POINT (-95.37040 29.70486)",
        )
        RasterRelatedModel.objects.create(rastermodel=model_instance)