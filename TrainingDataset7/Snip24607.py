def test_to_python_different_map_srid(self):
        f = forms.GeometryField(widget=OpenLayersWidget)
        json = '{ "type": "Point", "coordinates": [ 5.0, 23.0 ] }'
        self.assertEqual(
            GEOSGeometry("POINT(5 23)", srid=f.widget.map_srid), f.to_python(json)
        )