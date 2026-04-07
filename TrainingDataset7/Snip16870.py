def test_non_select_widget_cant_change_delete_related(self):
        main_band = Event._meta.get_field("main_band")
        widget = widgets.AdminRadioSelect()
        wrapper = widgets.RelatedFieldWidgetWrapper(
            widget,
            main_band,
            widget_admin_site,
            can_add_related=True,
            can_change_related=True,
            can_delete_related=True,
        )
        self.assertTrue(wrapper.can_add_related)
        self.assertFalse(wrapper.can_change_related)
        self.assertFalse(wrapper.can_delete_related)