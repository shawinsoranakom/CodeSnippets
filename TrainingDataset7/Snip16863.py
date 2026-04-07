def test_select_multiple_widget_cant_change_delete_related(self):
        rel = Individual._meta.get_field("parent").remote_field
        widget = forms.SelectMultiple()
        wrapper = widgets.RelatedFieldWidgetWrapper(
            widget,
            rel,
            widget_admin_site,
            can_add_related=True,
            can_change_related=True,
            can_delete_related=True,
        )
        self.assertTrue(wrapper.can_add_related)
        self.assertFalse(wrapper.can_change_related)
        self.assertFalse(wrapper.can_delete_related)