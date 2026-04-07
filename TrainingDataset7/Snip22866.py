def test_html_safe(self):
        class SimpleForm(Form):
            username = CharField()

        form = SimpleForm()
        self.assertTrue(hasattr(SimpleForm, "__html__"))
        self.assertEqual(str(form), form.__html__())
        self.assertTrue(hasattr(form["username"], "__html__"))
        self.assertEqual(str(form["username"]), form["username"].__html__())