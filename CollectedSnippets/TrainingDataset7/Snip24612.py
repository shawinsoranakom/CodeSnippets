def assertMapWidget(self, form_instance, geom_name):
        """
        Make sure the MapWidget js is passed in the form media and a MapWidget
        is actually created
        """
        self.assertTrue(form_instance.is_valid())
        rendered = form_instance.as_p()

        map_fields = [
            f for f in form_instance if isinstance(f.field, forms.GeometryField)
        ]
        for map_field in map_fields:
            attrs = {
                "base_layer": "nasaWorldview",
                "geom_type": map_field.field.geom_type,
                "map_srid": 3857,
                "display_raw": False,
                "required": True,
                "id": map_field.id_for_label,
                "geom_name": geom_name,
            }
            expected = json_script(attrs, f"{map_field.id_for_label}_mapwidget_options")
            self.assertInHTML(expected, rendered)
        self.assertIn("gis/js/OLMapWidget.js", str(form_instance.media))