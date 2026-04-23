def test_is_counterclockwise_geos_error(self):
        with mock.patch("django.contrib.gis.geos.prototypes.cs_is_ccw") as mocked:
            mocked.return_value = 0
            mocked.func_name = "GEOSCoordSeq_isCCW"
            msg = 'Error encountered in GEOS C function "GEOSCoordSeq_isCCW".'
            with self.assertRaisesMessage(GEOSException, msg):
                LinearRing((0, 0), (1, 0), (0, 1), (0, 0)).is_counterclockwise