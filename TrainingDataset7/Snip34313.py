def test_include_error(self):
        engine = Engine(dirs=[RELATIVE])
        msg = (
            "The relative path '\"./../three.html\"' points outside the file "
            "hierarchy that template 'error_include.html' is in."
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            engine.render_to_string("error_include.html")