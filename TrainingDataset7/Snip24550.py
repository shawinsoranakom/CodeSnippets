def test_dwithin_gis_lookup_output_with_rasters(self):
        """
        Check the logical functionality of the dwithin lookup for different
        input parameters.
        """
        # Create test raster and geom.
        rast = GDALRaster(json.loads(JSON_RASTER))
        stx_pnt = GEOSGeometry("POINT (-95.370401017314293 29.704867409475465)", 4326)
        stx_pnt.transform(3086)

        # Filter raster with different lookup raster formats.
        qs = RasterModel.objects.filter(rastprojected__dwithin=(rast, D(km=1)))
        self.assertEqual(qs.count(), 1)

        qs = RasterModel.objects.filter(
            rastprojected__dwithin=(json.loads(JSON_RASTER), D(km=1))
        )
        self.assertEqual(qs.count(), 1)

        qs = RasterModel.objects.filter(rastprojected__dwithin=(JSON_RASTER, D(km=1)))
        self.assertEqual(qs.count(), 1)

        # Filter in an unprojected coordinate system.
        qs = RasterModel.objects.filter(rast__dwithin=(rast, 40))
        self.assertEqual(qs.count(), 1)

        # Filter with band index transform.
        qs = RasterModel.objects.filter(rast__1__dwithin=(rast, 1, 40))
        self.assertEqual(qs.count(), 1)
        qs = RasterModel.objects.filter(rast__1__dwithin=(rast, 40))
        self.assertEqual(qs.count(), 1)
        qs = RasterModel.objects.filter(rast__dwithin=(rast, 1, 40))
        self.assertEqual(qs.count(), 1)

        # Filter raster by geom.
        qs = RasterModel.objects.filter(rast__dwithin=(stx_pnt, 500))
        self.assertEqual(qs.count(), 1)

        qs = RasterModel.objects.filter(rastprojected__dwithin=(stx_pnt, D(km=10000)))
        self.assertEqual(qs.count(), 1)

        qs = RasterModel.objects.filter(rast__dwithin=(stx_pnt, 5))
        self.assertEqual(qs.count(), 0)

        qs = RasterModel.objects.filter(rastprojected__dwithin=(stx_pnt, D(km=100)))
        self.assertEqual(qs.count(), 0)

        # Filter geom by raster.
        qs = RasterModel.objects.filter(geom__dwithin=(rast, 500))
        self.assertEqual(qs.count(), 1)

        # Filter through related model.
        qs = RasterRelatedModel.objects.filter(rastermodel__rast__dwithin=(rast, 40))
        self.assertEqual(qs.count(), 1)

        # Filter through related model with band index transform
        qs = RasterRelatedModel.objects.filter(rastermodel__rast__1__dwithin=(rast, 40))
        self.assertEqual(qs.count(), 1)

        # Filter through conditional statements.
        qs = RasterModel.objects.filter(
            Q(rast__dwithin=(rast, 40))
            & Q(rastprojected__dwithin=(stx_pnt, D(km=10000)))
        )
        self.assertEqual(qs.count(), 1)

        # Filter through different lookup.
        qs = RasterModel.objects.filter(rastprojected__bbcontains=rast)
        self.assertEqual(qs.count(), 1)