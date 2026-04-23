def test_widget_is_hidden(self):
        rel = Album._meta.get_field("band").remote_field
        widget = forms.HiddenInput()
        widget.choices = ()
        wrapper = widgets.RelatedFieldWidgetWrapper(widget, rel, widget_admin_site)
        self.assertIs(wrapper.is_hidden, True)
        context = wrapper.get_context("band", None, {})
        self.assertIs(context["is_hidden"], True)
        output = wrapper.render("name", "value")
        # Related item links are hidden.
        self.assertNotIn("<a ", output)