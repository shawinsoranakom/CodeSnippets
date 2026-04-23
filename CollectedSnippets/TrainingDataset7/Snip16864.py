def test_on_delete_cascade_rel_cant_delete_related(self):
        rel = Individual._meta.get_field("soulmate").remote_field
        widget = forms.Select()
        wrapper = widgets.RelatedFieldWidgetWrapper(
            widget,
            rel,
            widget_admin_site,
            can_add_related=True,
            can_change_related=True,
            can_delete_related=True,
        )
        self.assertTrue(wrapper.can_add_related)
        self.assertTrue(wrapper.can_change_related)
        self.assertFalse(wrapper.can_delete_related)