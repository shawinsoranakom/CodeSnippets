def test_widget_is_not_hidden(self):
        rel = Album._meta.get_field("band").remote_field
        widget = forms.Select()
        wrapper = widgets.RelatedFieldWidgetWrapper(widget, rel, widget_admin_site)
        self.assertIs(wrapper.is_hidden, False)
        context = wrapper.get_context("band", None, {})
        self.assertIs(context["is_hidden"], False)
        output = wrapper.render("name", "value")
        # Related item links are present.
        self.assertIn("<a ", output)