def test_select_aria_describedby(self):
        class TestForm(Form):
            color = MultipleChoiceField(
                choices=[("red", "Red"), ("green", "Green")],
                help_text="Select Color",
            )

        f = TestForm({"color": "Blue"})
        self.assertHTMLEqual(
            str(f),
            '<div><label for="id_color">Color:</label><div class="helptext" '
            'id="id_color_helptext">Select Color</div>'
            '<ul class="errorlist" id="id_color_error"><li>Enter a list of values.'
            '</li></ul><select name="color" required aria-invalid="true" '
            'aria-describedby="id_color_helptext id_color_error" id="id_color" '
            'multiple><option value="red">Red</option>'
            '<option value="green">Green</option></select></div>',
        )