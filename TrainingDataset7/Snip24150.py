def test_geojson(self):
        """
        Test GeoJSON() function with Z values.
        """
        self._load_city_data()
        h = City3D.objects.annotate(geojson=AsGeoJSON("point", precision=6)).get(
            name="Houston"
        )
        # GeoJSON should be 3D
        # `SELECT ST_AsGeoJSON(point, 6) FROM geo3d_city3d
        #     WHERE name='Houston';`
        ref_json_regex = re.compile(
            r'^{"type":"Point","coordinates":\[-95.363151,29.763374,18(\.0+)?\]}$'
        )
        self.assertTrue(ref_json_regex.match(h.geojson))