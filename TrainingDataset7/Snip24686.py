def test_add_entry(self):
        """
        Test adding a new entry in the SpatialRefSys model using the
        add_srs_entry utility.
        """
        from django.contrib.gis.utils import add_srs_entry

        add_srs_entry(3857)
        self.assertTrue(self.SpatialRefSys.objects.filter(srid=3857).exists())
        srs = self.SpatialRefSys.objects.get(srid=3857)
        self.assertTrue(
            self.SpatialRefSys.get_spheroid(srs.wkt).startswith("SPHEROID[")
        )