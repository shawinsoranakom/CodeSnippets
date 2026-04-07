def test_translate_and_plural_blocktranslate_collision(self):
        """
        Ensures a correct workaround for the gettext bug when handling a
        literal found inside a {% translate %} tag and also in another file
        inside a {% blocktranslate %} with a plural (#17375).
        """
        management.call_command(
            "makemessages", locale=[LOCALE], extensions=["html", "djtpl"], verbosity=0
        )
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()
            self.assertNotIn(
                "#-#-#-#-#  django.pot (PACKAGE VERSION)  #-#-#-#-#\\n", po_contents
            )
            self.assertMsgId(
                "First `translate`, then `blocktranslate` with a plural", po_contents
            )
            self.assertMsgIdPlural(
                "Plural for a `translate` and `blocktranslate` collision case",
                po_contents,
            )