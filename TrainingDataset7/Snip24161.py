def test_custom_gis_widget_kwargs(self):
        geoadmin = site_gis_custom.get_model_admin(City)
        form = geoadmin.get_changelist_form(None)()
        widget = form["point"].field.widget
        self.assertEqual(widget.attrs["default_lat"], 55)
        self.assertEqual(widget.attrs["default_lon"], 37)
        self.assertEqual(widget.attrs["default_zoom"], 12)