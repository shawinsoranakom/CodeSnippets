def test_add_raster_field_on_db_without_raster_support(self):
        msg = "Raster fields require backends with raster support."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.set_up_test_model()
            self.alter_gis_model(
                migrations.AddField, "Neighborhood", "heatmap", fields.RasterField
            )