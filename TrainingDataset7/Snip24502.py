def test_create_raster_model_on_db_without_raster_support(self):
        msg = "Raster fields require backends with raster support."
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.set_up_test_model(force_raster_creation=True)