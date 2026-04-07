def test_multi_widget(self):
        ###############################################################
        # Multiwidget media handling
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

        # MultiWidgets have a default media definition that gets all the
        # media from the component widgets
        class MyMultiWidget(MultiWidget):
            def __init__(self, attrs=None):
                widgets = [MyWidget1, MyWidget2, MyWidget3]
                super().__init__(widgets, attrs)

        mymulti = MyMultiWidget()
        self.assertEqual(
            str(mymulti.media),
            '<link href="http://media.example.com/static/path/to/css1" media="all" '
            'rel="stylesheet">\n'
            '<link href="/path/to/css2" media="all" rel="stylesheet">\n'
            '<link href="/path/to/css3" media="all" rel="stylesheet">\n'
            '<script src="/path/to/js1"></script>\n'
            '<script src="http://media.other.com/path/to/js2"></script>\n'
            '<script src="/path/to/js4"></script>\n'
            '<script src="https://secure.other.com/path/to/js3"></script>',
        )