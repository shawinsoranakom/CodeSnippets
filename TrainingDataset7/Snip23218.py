def nested_widgets(self):
        nested_widget = self.widget(
            choices=(
                ("outer1", "Outer 1"),
                ('Group "1"', (("inner1", "Inner 1"), ("inner2", "Inner 2"))),
            ),
        )
        nested_widget_dict = self.widget(
            choices={
                "outer1": "Outer 1",
                'Group "1"': {"inner1": "Inner 1", "inner2": "Inner 2"},
            },
        )
        nested_widget_dict_tuple = self.widget(
            choices={
                "outer1": "Outer 1",
                'Group "1"': (("inner1", "Inner 1"), ("inner2", "Inner 2")),
            },
        )
        return (nested_widget, nested_widget_dict, nested_widget_dict_tuple)