def test_disabled_parameter_id(self, widget_func):
        widget_func("my_widget")

        # The `disabled` argument shouldn't affect a widget's ID, so we
        # expect a DuplicateWidgetID error.
        with self.assertRaises(errors.DuplicateWidgetID):
            widget_func("my_widget", disabled=True)