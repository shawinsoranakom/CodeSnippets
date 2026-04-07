def test_widget_delegates_value_omitted_from_data(self):
        class CustomWidget(forms.Select):
            def value_omitted_from_data(self, data, files, name):
                return False

        rel = Album._meta.get_field("band").remote_field
        widget = CustomWidget()
        wrapper = widgets.RelatedFieldWidgetWrapper(widget, rel, widget_admin_site)
        self.assertIs(wrapper.value_omitted_from_data({}, {}, "band"), False)