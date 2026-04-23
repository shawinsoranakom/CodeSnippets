def test_charfield_widget_attrs(self):
        """
        CharField.widget_attrs() always returns a dictionary and includes
        minlength/maxlength if min_length/max_length are defined on the field
        and the widget is not hidden.
        """
        # Return an empty dictionary if max_length and min_length are both
        # None.
        f = CharField()
        self.assertEqual(f.widget_attrs(TextInput()), {})
        self.assertEqual(f.widget_attrs(Textarea()), {})

        # Return a maxlength attribute equal to max_length.
        f = CharField(max_length=10)
        self.assertEqual(f.widget_attrs(TextInput()), {"maxlength": "10"})
        self.assertEqual(f.widget_attrs(PasswordInput()), {"maxlength": "10"})
        self.assertEqual(f.widget_attrs(Textarea()), {"maxlength": "10"})

        # Return a minlength attribute equal to min_length.
        f = CharField(min_length=5)
        self.assertEqual(f.widget_attrs(TextInput()), {"minlength": "5"})
        self.assertEqual(f.widget_attrs(PasswordInput()), {"minlength": "5"})
        self.assertEqual(f.widget_attrs(Textarea()), {"minlength": "5"})

        # Return both maxlength and minlength when both max_length and
        # min_length are set.
        f = CharField(max_length=10, min_length=5)
        self.assertEqual(
            f.widget_attrs(TextInput()), {"maxlength": "10", "minlength": "5"}
        )
        self.assertEqual(
            f.widget_attrs(PasswordInput()), {"maxlength": "10", "minlength": "5"}
        )
        self.assertEqual(
            f.widget_attrs(Textarea()), {"maxlength": "10", "minlength": "5"}
        )
        self.assertEqual(f.widget_attrs(HiddenInput()), {})