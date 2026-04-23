def test_aria_describedby_property(self):
        class TestForm(Form):
            name = CharField(help_text="Some help text")

        form = TestForm({"name": "MyName"})
        self.assertEqual(form["name"].aria_describedby, "id_name_helptext")

        form = TestForm(auto_id=None)
        self.assertEqual(form["name"].aria_describedby, "")

        class TestFormHidden(Form):
            name = CharField(help_text="Some help text", widget=HiddenInput)

        form = TestFormHidden()
        self.assertEqual(form["name"].aria_describedby, "")

        class TestFormWithAttrs(Form):
            name = CharField(widget=TextInput(attrs={"aria-describedby": "my-id"}))

        form = TestFormWithAttrs({"name": "MyName"})
        self.assertIs(form["name"].aria_describedby, None)

        class TestFormWithoutHelpText(Form):
            name = CharField()

        form = TestFormWithoutHelpText()
        self.assertEqual(form["name"].aria_describedby, "")