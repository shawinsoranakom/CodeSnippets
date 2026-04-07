def test_default_gis_widget_kwargs(self):
        geoadmin = self.admin_site.get_model_admin(City)
        form = geoadmin.get_changelist_form(None)()
        widget = form["point"].field.widget
        self.assertEqual(widget.attrs["default_lat"], 47)
        self.assertEqual(widget.attrs["default_lon"], 5)
        self.assertEqual(widget.attrs["default_zoom"], 12)