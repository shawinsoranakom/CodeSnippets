def test_json(self):
        "Testing GeoJSON input/output."
        for g in self.geometries.json_geoms:
            geom = OGRGeometry(g.wkt)
            if not hasattr(g, "not_equal"):
                # Loading jsons to prevent decimal differences
                self.assertEqual(json.loads(g.json), json.loads(geom.json))
                self.assertEqual(json.loads(g.json), json.loads(geom.geojson))
            self.assertEqual(OGRGeometry(g.wkt), OGRGeometry(geom.json))
        # Test input with some garbage content (but valid json) (#15529)
        geom = OGRGeometry(
            '{"type": "Point", "coordinates": [ 100.0, 0.0 ], "other": "<test>"}'
        )
        self.assertIsInstance(geom, OGRGeometry)