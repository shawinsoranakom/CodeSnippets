def test_kml(self):
        """
        Test KML() function with Z values.
        """
        self._load_city_data()
        h = City3D.objects.annotate(kml=AsKML("point", precision=6)).get(name="Houston")
        # KML should be 3D.
        # `SELECT ST_AsKML(point, 6) FROM geo3d_city3d WHERE name = 'Houston';`
        ref_kml_regex = re.compile(
            r"^<Point><coordinates>-95.363\d+,29.763\d+,18</coordinates></Point>$"
        )
        self.assertTrue(ref_kml_regex.match(h.kml))