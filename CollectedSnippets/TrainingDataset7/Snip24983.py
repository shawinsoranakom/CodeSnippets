def test_extraction_error(self):
        msg = (
            "Translation blocks must not include other block tags: blocktranslate "
            "(file %s, line 3)" % os.path.join("templates", "template_with_error.tpl")
        )
        with self.assertRaisesMessage(SyntaxError, msg):
            management.call_command(
                "makemessages", locale=[LOCALE], extensions=["tpl"], verbosity=0
            )
        # The temporary files were cleaned up.
        self.assertFalse(os.path.exists("./templates/template_with_error.tpl.py"))
        self.assertFalse(os.path.exists("./templates/template_0_with_no_error.tpl.py"))