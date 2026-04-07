def assertTextarea(self, geom, rendered):
        """Makes sure the wkt and a textarea are in the content"""

        self.assertIn("<textarea ", rendered)
        self.assertIn("required", rendered)
        ogr = geom.ogr
        ogr.transform(3857)
        self.assertIn(escape(ogr.json), rendered)