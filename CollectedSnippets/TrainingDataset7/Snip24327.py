def test_json_srid(self):
        geojson_data = {
            "type": "Point",
            "coordinates": [2, 49],
            "crs": {
                "type": "name",
                "properties": {"name": "urn:ogc:def:crs:EPSG::4322"},
            },
        }
        self.assertEqual(
            GEOSGeometry(json.dumps(geojson_data)), Point(2, 49, srid=4322)
        )