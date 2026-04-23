def test_osm_widget(self):
        class PointForm(forms.Form):
            p = forms.PointField(widget=forms.OSMWidget)

        geom = self.geometries["point"]
        form = PointForm(data={"p": geom})
        rendered = form.as_p()

        self.assertIn('"base_layer": "osm"', rendered)
        self.assertIn('<textarea id="id_p"', rendered)