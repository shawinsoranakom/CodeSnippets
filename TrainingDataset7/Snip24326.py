def test_json(self):
        "Testing GeoJSON input/output (via GDAL)."
        for g in self.geometries.json_geoms:
            geom = GEOSGeometry(g.wkt)
            with self.subTest(g=g):
                if not hasattr(g, "not_equal"):
                    # Loading jsons to prevent decimal differences
                    self.assertEqual(json.loads(g.json), json.loads(geom.json))
                    self.assertEqual(json.loads(g.json), json.loads(geom.geojson))
                self.assertEqual(GEOSGeometry(g.wkt, 4326), GEOSGeometry(geom.json))