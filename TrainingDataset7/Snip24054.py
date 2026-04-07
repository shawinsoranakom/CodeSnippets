def test_from_gml(self):
        self.assertEqual(
            OGRGeometry("POINT(0 0)"),
            OGRGeometry.from_gml(
                '<gml:Point gml:id="p21" '
                'srsName="http://www.opengis.net/def/crs/EPSG/0/4326">'
                '    <gml:pos srsDimension="2">0 0</gml:pos>'
                "</gml:Point>"
            ),
        )