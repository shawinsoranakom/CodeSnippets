def test_disabled_parameter_id_options_widgets(self, widget_func):
        options = ["a", "b", "c"]
        widget_func("my_widget", options)

        with self.assertRaises(errors.DuplicateWidgetID):
            widget_func("my_widget", options, disabled=True)