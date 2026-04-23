def test_textarea_aria_describedby(self):
        class TestForm(Form):
            color = CharField(widget=Textarea, max_length=5, help_text="Enter Color")

        f = TestForm({"color": "Purple"})
        self.assertHTMLEqual(
            str(f),
            '<div><label for="id_color">Color:</label>'
            '<div class="helptext" id="id_color_helptext">Enter Color</div>'
            '<ul class="errorlist" id="id_color_error">'
            "<li>Ensure this value has at most 5 characters (it has 6).</li></ul>"
            '<textarea name="color" cols="40" rows="10" maxlength="5" required '
            'aria-invalid="true" aria-describedby="id_color_helptext id_color_error" '
            'id="id_color">Purple</textarea></div>',
        )