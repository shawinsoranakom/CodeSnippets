def test_boundfield_widget_type(self):
        class SomeForm(Form):
            first_name = CharField()
            birthday = SplitDateTimeField(widget=SplitHiddenDateTimeWidget)

        f = SomeForm()
        self.assertEqual(f["first_name"].widget_type, "text")
        self.assertEqual(f["birthday"].widget_type, "splithiddendatetime")