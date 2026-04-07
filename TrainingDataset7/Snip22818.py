def test_aria_describedby_called_multiple_times(self):
        class TestForm(Form):
            color = CharField(widget=Textarea, help_text="Enter Color")

        f = TestForm({"color": "Purple"})
        self.assertEqual(f["color"].aria_describedby, "id_color_helptext")
        f.add_error("color", "An error about Purple.")
        self.assertEqual(
            f["color"].aria_describedby, "id_color_helptext id_color_error"
        )