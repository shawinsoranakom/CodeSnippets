def test_default_lat_lon(self):
        self.assertEqual(forms.OSMWidget.default_lon, 5)
        self.assertEqual(forms.OSMWidget.default_lat, 47)
        self.assertEqual(forms.OSMWidget.default_zoom, 12)

        class PointForm(forms.Form):
            p = forms.PointField(
                widget=forms.OSMWidget(
                    attrs={
                        "default_lon": 20,
                        "default_lat": 30,
                        "default_zoom": 17,
                    }
                ),
            )

        form = PointForm()
        rendered = form.as_p()

        attrs = {
            "base_layer": "osm",
            "geom_type": "POINT",
            "map_srid": 3857,
            "display_raw": False,
            "default_lon": 20,
            "default_lat": 30,
            "default_zoom": 17,
            "required": True,
            "id": "id_p",
            "geom_name": "Point",
        }
        expected = json_script(attrs, "id_p_mapwidget_options")
        self.assertInHTML(expected, rendered)