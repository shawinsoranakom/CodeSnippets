def test_3d_layermapping(self):
        """
        Testing LayerMapping on 3D models.
        """
        # Import here as GDAL is required for those imports
        from django.contrib.gis.utils import LayerMapError, LayerMapping

        point_mapping = {"point": "POINT"}
        mpoint_mapping = {"mpoint": "MULTIPOINT"}

        # The VRT is 3D, but should still be able to map sans the Z.
        lm = LayerMapping(Point2D, vrt_file, point_mapping, transform=False)
        lm.save()
        self.assertEqual(3, Point2D.objects.count())

        # The city shapefile is 2D, and won't be able to fill the coordinates
        # in the 3D model -- thus, a LayerMapError is raised.
        with self.assertRaises(LayerMapError):
            LayerMapping(Point3D, city_file, point_mapping, transform=False)

        # 3D model should take 3D data just fine.
        lm = LayerMapping(Point3D, vrt_file, point_mapping, transform=False)
        lm.save()
        self.assertEqual(3, Point3D.objects.count())

        # Making sure LayerMapping.make_multi works right, by converting
        # a Point25D into a MultiPoint25D.
        lm = LayerMapping(MultiPoint3D, vrt_file, mpoint_mapping, transform=False)
        lm.save()
        self.assertEqual(3, MultiPoint3D.objects.count())