def test_override_attrs(self):
        self.assertIsNone(forms.BaseGeometryWidget.base_layer)
        self.assertEqual(forms.BaseGeometryWidget.geom_type, "GEOMETRY")
        self.assertEqual(forms.BaseGeometryWidget.map_srid, 4326)
        self.assertIs(forms.BaseGeometryWidget.display_raw, False)

        class PointForm(forms.Form):
            p = forms.PointField(
                widget=forms.OpenLayersWidget(
                    attrs={
                        "base_layer": "some-test-file",
                        "map_srid": 1234,
                    }
                ),
            )

        form = PointForm()
        rendered = form.as_p()

        attrs = {
            "base_layer": "some-test-file",
            "geom_type": "POINT",
            "map_srid": 1234,
            "display_raw": False,
            "required": True,
            "id": "id_p",
            "geom_name": "Point",
        }
        expected = json_script(attrs, "id_p_mapwidget_options")
        self.assertInHTML(expected, rendered)