def test_no_can_add_related(self):
        rel = Individual._meta.get_field("parent").remote_field
        w = widgets.AdminRadioSelect()
        # Used to fail with a name error.
        w = widgets.RelatedFieldWidgetWrapper(w, rel, widget_admin_site)
        self.assertFalse(w.can_add_related)