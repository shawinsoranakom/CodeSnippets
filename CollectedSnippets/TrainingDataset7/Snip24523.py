def test_invalid_layer(self):
        "Tests LayerMapping on invalid geometries. See #15378."
        invalid_mapping = {"point": "POINT"}
        lm = LayerMapping(Invalid, invalid_shp, invalid_mapping, source_srs=4326)
        lm.save(silent=True)