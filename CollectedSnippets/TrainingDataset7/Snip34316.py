def test_mixing_loop(self):
        engine = Engine(dirs=[RELATIVE])
        msg = (
            "The relative path '\"./dir2/../looped.html\"' was translated to "
            "template name 'dir1/looped.html', the same template in which "
            "the tag appears."
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            engine.render_to_string("dir1/looped.html")