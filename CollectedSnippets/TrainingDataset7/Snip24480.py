def set_up_test_model(self, force_raster_creation=False):
        test_fields = [
            ("id", models.AutoField(primary_key=True)),
            ("name", models.CharField(max_length=100, unique=True)),
            ("geom", fields.MultiPolygonField(srid=4326)),
        ]
        if connection.features.supports_raster or force_raster_creation:
            test_fields += [("rast", fields.RasterField(srid=4326, null=True))]
        operations = [migrations.CreateModel("Neighborhood", test_fields)]
        self.current_state = self.apply_operations("gis", ProjectState(), operations)