def test_remove_raster_field(self):
        """
        Test the RemoveField operation with a raster-enabled column.
        """
        self.alter_gis_model(migrations.RemoveField, "Neighborhood", "rast")
        self.assertColumnNotExists("gis_neighborhood", "rast")