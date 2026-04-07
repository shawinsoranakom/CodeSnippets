def test_alter_geom_field_dim(self):
        Neighborhood = self.current_state.apps.get_model("gis", "Neighborhood")
        p1 = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))
        Neighborhood.objects.create(name="TestDim", geom=MultiPolygon(p1, p1))
        # Add 3rd dimension.
        self.alter_gis_model(
            migrations.AlterField,
            "Neighborhood",
            "geom",
            fields.MultiPolygonField,
            field_class_kwargs={"dim": 3},
        )
        self.assertTrue(Neighborhood.objects.first().geom.hasz)
        # Rewind to 2 dimensions.
        self.alter_gis_model(
            migrations.AlterField,
            "Neighborhood",
            "geom",
            fields.MultiPolygonField,
            field_class_kwargs={"dim": 2},
        )
        self.assertFalse(Neighborhood.objects.first().geom.hasz)