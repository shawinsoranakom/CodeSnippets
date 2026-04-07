def test_get_context(self):
        self.assertEqual(
            SplitArrayWidget(forms.TextInput(), size=2).get_context(
                "name", ["val1", "val2"]
            ),
            {
                "widget": {
                    "name": "name",
                    "is_hidden": False,
                    "required": False,
                    "value": "['val1', 'val2']",
                    "attrs": {},
                    "template_name": "postgres/widgets/split_array.html",
                    "subwidgets": [
                        {
                            "name": "name_0",
                            "is_hidden": False,
                            "required": False,
                            "value": "val1",
                            "attrs": {},
                            "template_name": "django/forms/widgets/text.html",
                            "type": "text",
                        },
                        {
                            "name": "name_1",
                            "is_hidden": False,
                            "required": False,
                            "value": "val2",
                            "attrs": {},
                            "template_name": "django/forms/widgets/text.html",
                            "type": "text",
                        },
                    ],
                }
            },
        )