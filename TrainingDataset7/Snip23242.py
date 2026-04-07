def test_fieldset(self):
        class TestForm(Form):
            template_name = "forms_tests/use_fieldset.html"
            field = FileField(widget=self.widget)
            with_file = FileField(widget=self.widget, initial=FakeFieldFile())
            clearable_file = FileField(
                widget=self.widget, initial=FakeFieldFile(), required=False
            )

        form = TestForm()
        self.assertIs(self.widget.use_fieldset, False)
        self.assertHTMLEqual(
            '<div><label for="id_field">Field:</label>'
            '<input id="id_field" name="field" type="file" required></div>'
            '<div><label for="id_with_file">With file:</label>Currently: '
            '<a href="something">something</a><br>Change:<input type="file" '
            'name="with_file" id="id_with_file"></div>'
            '<div><label for="id_clearable_file">Clearable file:</label>'
            'Currently: <a href="something">something</a><input '
            'type="checkbox" name="clearable_file-clear" id="clearable_file-clear_id">'
            '<label for="clearable_file-clear_id">Clear</label><br>Change:'
            '<input type="file" name="clearable_file" id="id_clearable_file"></div>',
            form.render(),
        )