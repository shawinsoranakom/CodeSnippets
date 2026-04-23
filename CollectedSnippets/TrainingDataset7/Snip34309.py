def test_extend_error(self):
        engine = Engine(dirs=[RELATIVE])
        msg = (
            "The relative path '\"./../two.html\"' points outside the file "
            "hierarchy that template 'error_extends.html' is in."
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            engine.render_to_string("error_extends.html")