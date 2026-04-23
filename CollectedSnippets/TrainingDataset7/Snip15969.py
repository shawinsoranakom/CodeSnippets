def test_safestring_in_field_label(self):
        # safestring should not be escaped
        class MyForm(forms.Form):
            text = forms.CharField(label=mark_safe("<i>text</i>"))
            cb = forms.BooleanField(label=mark_safe("<i>cb</i>"))

        form = MyForm()
        self.assertHTMLEqual(
            helpers.AdminField(form, "text", is_first=False).label_tag(),
            '<label for="id_text" class="required inline"><i>text</i>:</label>',
        )
        self.assertHTMLEqual(
            helpers.AdminField(form, "cb", is_first=False).label_tag(),
            '<label for="id_cb" class="vCheckboxLabel required inline">'
            "<i>cb</i></label>",
        )

        # normal strings needs to be escaped
        class MyForm(forms.Form):
            text = forms.CharField(label="&text")
            cb = forms.BooleanField(label="&cb")

        form = MyForm()
        self.assertHTMLEqual(
            helpers.AdminField(form, "text", is_first=False).label_tag(),
            '<label for="id_text" class="required inline">&amp;text:</label>',
        )
        self.assertHTMLEqual(
            helpers.AdminField(form, "cb", is_first=False).label_tag(),
            '<label for="id_cb" class="vCheckboxLabel required inline">&amp;cb</label>',
        )