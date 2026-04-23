def test_custom_widget_render(self):
        class CustomWidget(forms.Select):
            def render(self, *args, **kwargs):
                return "custom render output"

        rel = Album._meta.get_field("band").remote_field
        widget = CustomWidget()
        wrapper = widgets.RelatedFieldWidgetWrapper(
            widget,
            rel,
            widget_admin_site,
            can_add_related=True,
            can_change_related=True,
            can_delete_related=True,
        )
        output = wrapper.render("name", "value")
        self.assertIn("custom render output", output)