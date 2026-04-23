def test_polygons_templates(self):
        # Accessing Polygon attributes in templates should work.
        engine = Engine()
        template = engine.from_string("{{ polygons.0.wkt }}")
        polygons = [fromstr(p.wkt) for p in self.geometries.multipolygons[:2]]
        content = template.render(Context({"polygons": polygons}))
        self.assertIn("MULTIPOLYGON (((100", content)