def test_error_escaping(self):
        class TestForm(Form):
            hidden = CharField(widget=HiddenInput(), required=False)
            visible = CharField()

            def clean_hidden(self):
                raise ValidationError('Foo & "bar"!')

            clean_visible = clean_hidden

        form = TestForm({"hidden": "a", "visible": "b"})
        form.is_valid()
        self.assertHTMLEqual(
            form.as_ul(),
            '<li><ul class="errorlist nonfield">'
            "<li>(Hidden field hidden) Foo &amp; &quot;bar&quot;!</li></ul></li>"
            '<li><ul class="errorlist" id="id_visible_error"><li>Foo &amp; '
            "&quot;bar&quot;!</li></ul>"
            '<label for="id_visible">Visible:</label> '
            '<input type="text" name="visible" aria-invalid="true" value="b" '
            'id="id_visible" required aria-describedby="id_visible_error">'
            '<input type="hidden" name="hidden" value="a" id="id_hidden"></li>',
        )