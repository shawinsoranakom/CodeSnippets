def test_iterate_radios(self):
        f = FrameworkForm(auto_id="id_%s")
        t = Template(
            "{% for radio in form.language %}"
            '<div class="myradio">{{ radio }}</div>'
            "{% endfor %}"
        )
        self.assertHTMLEqual(
            t.render(Context({"form": f})),
            '<div class="myradio"><label for="id_language_0">'
            '<input id="id_language_0" name="language" type="radio" value="P" '
            "required> Python</label></div>"
            '<div class="myradio"><label for="id_language_1">'
            '<input id="id_language_1" name="language" type="radio" value="J" '
            "required> Java</label></div>",
        )