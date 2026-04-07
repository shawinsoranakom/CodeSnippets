def test_form_media(self):
        ###############################################################
        # Media processing for forms
        ###############################################################

        class MyWidget1(TextInput):
            class Media:
                css = {"all": ("path/to/css1", "/path/to/css2")}
                js = (
                    "/path/to/js1",
                    "http://media.other.com/path/to/js2",
                    "https://secure.other.com/path/to/js3",
                )

        class MyWidget2(TextInput):
            class Media:
                css = {"all": ("/path/to/css2", "/path/to/css3")}
                js = ("/path/to/js1", "/path/to/js4")

        class MyWidget3(TextInput):
            class Media:
                css = {"all": ("path/to/css1", "/path/to/css3")}
                js = ("/path/to/js1", "/path/to/js4")

        # You can ask a form for the media required by its widgets.
        class MyForm(Form):
            field1 = CharField(max_length=20, widget=MyWidget1())
            field2 = CharField(max_length=20, widget=MyWidget2())

        f1 = MyForm()
        self.assertEqual(
            str(f1.media),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<link href="/path/to/css3" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="/path/to/js4"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )

        # Form media can be combined to produce a single media definition.
        class AnotherForm(Form):
            field3 = CharField(max_length=20, widget=MyWidget3())

        f2 = AnotherForm()
        self.assertEqual(
            str(f1.media + f2.media),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<link href="/path/to/css3" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="/path/to/js4"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )

        # Forms can also define media, following the same rules as widgets.
        class FormWithMedia(Form):
            field1 = CharField(max_length=20, widget=MyWidget1())
            field2 = CharField(max_length=20, widget=MyWidget2())

            class Media:
                js = ("/some/form/javascript",)
                css = {"all": ("/some/form/css",)}

        f3 = FormWithMedia()
        self.assertEqual(
            str(f3.media),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/some/form/css" media="all" rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<link href="/path/to/css3" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="/some/form/javascript"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="/path/to/js4"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )

        # Media works in templates
        self.assertEqual(
            Template("{{ form.media.js }}{{ form.media.css }}").render(
                Context({"form": f3})
            ),
            '<script src="/path/to/js1"></script>\n'
            '<script src="/some/form/javascript"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="/path/to/js4"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>'
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/some/form/css" media="all" rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<link href="/path/to/css3" media="all" rel="stylesheet">',
        )