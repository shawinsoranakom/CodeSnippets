def test_asgml(self):
        # Should throw a TypeError when trying to obtain GML from a
        # non-geometry field.
        qs = City.objects.all()
        with self.assertRaises(TypeError):
            qs.annotate(gml=functions.AsGML("name"))
        ptown = City.objects.annotate(gml=functions.AsGML("point", precision=9)).get(
            name="Pueblo"
        )

        if connection.ops.oracle:
            # No precision parameter for Oracle :-/
            gml_regex = re.compile(
                r'^<gml:Point srsName="EPSG:4326" '
                r'xmlns:gml="http://www.opengis.net/gml">'
                r'<gml:coordinates decimal="\." cs="," ts=" ">'
                r"-104.60925\d+,38.25500\d+ "
                r"</gml:coordinates></gml:Point>"
            )
        else:
            gml_regex = re.compile(
                r'^<gml:Point srsName="(urn:ogc:def:crs:)?EPSG:4326"><gml:coordinates>'
                r"-104\.60925\d+,38\.255001</gml:coordinates></gml:Point>"
            )
        self.assertTrue(gml_regex.match(ptown.gml))
        self.assertIn(
            '<gml:pos srsDimension="2">',
            City.objects.annotate(gml=functions.AsGML("point", version=3))
            .get(name="Pueblo")
            .gml,
        )