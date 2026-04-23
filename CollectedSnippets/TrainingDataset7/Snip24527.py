def test_null_geom_with_unique(self):
        """LayerMapping may be created with a unique and a null geometry."""
        State.objects.bulk_create(
            [State(name="Colorado"), State(name="Hawaii"), State(name="Texas")]
        )
        hw = State.objects.get(name="Hawaii")
        hu = County.objects.create(name="Honolulu", state=hw, mpoly=None)
        lm = LayerMapping(County, co_shp, co_mapping, transform=False, unique="name")
        lm.save(silent=True, strict=True)
        hu.refresh_from_db()
        self.assertIsNotNone(hu.mpoly)
        self.assertEqual(hu.mpoly.ogr.num_coords, 449)