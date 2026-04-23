def test_build_attrs(self):
        form = AlbumForm()
        attrs = form["band"].field.widget.get_context(
            name="my_field", value=None, attrs={}
        )["widget"]["attrs"]
        self.assertEqual(
            attrs,
            {
                "class": "my-class admin-autocomplete",
                "data-ajax--cache": "true",
                "data-ajax--delay": 250,
                "data-ajax--type": "GET",
                "data-ajax--url": "/autocomplete/",
                "data-theme": "admin-autocomplete",
                "data-allow-clear": "false",
                "data-app-label": "admin_widgets",
                "data-field-name": "band",
                "data-model-name": "album",
                "data-placeholder": "",
                "lang": "en",
            },
        )