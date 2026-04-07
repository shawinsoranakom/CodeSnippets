def test_subwidgets(self):
        widget = forms.BaseGeometryWidget()
        self.assertEqual(
            list(widget.subwidgets("name", "value")),
            [
                {
                    "is_hidden": False,
                    "attrs": {
                        "base_layer": None,
                        "display_raw": False,
                        "map_srid": 4326,
                        "geom_name": "Geometry",
                        "geom_type": "GEOMETRY",
                    },
                    "name": "name",
                    "template_name": "",
                    "value": "value",
                    "required": False,
                }
            ],
        )