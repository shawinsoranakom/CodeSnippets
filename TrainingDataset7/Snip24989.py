def test_template_comments(self):
        """
        Template comment tags on the same line of other constructs (#19552)
        """
        # Test detection/end user reporting of old, incorrect templates
        # translator comments syntax
        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            management.call_command(
                "makemessages", locale=[LOCALE], extensions=["thtml"], verbosity=0
            )
            self.assertEqual(len(ws), 3)
            for w in ws:
                self.assertTrue(issubclass(w.category, TranslatorCommentWarning))
            self.assertRegex(
                str(ws[0].message),
                r"The translator-targeted comment 'Translators: ignored i18n "
                r"comment #1' \(file templates[/\\]comments.thtml, line 4\) "
                r"was ignored, because it wasn't the last item on the line\.",
            )
            self.assertRegex(
                str(ws[1].message),
                r"The translator-targeted comment 'Translators: ignored i18n "
                r"comment #3' \(file templates[/\\]comments.thtml, line 6\) "
                r"was ignored, because it wasn't the last item on the line\.",
            )
            self.assertRegex(
                str(ws[2].message),
                r"The translator-targeted comment 'Translators: ignored i18n "
                r"comment #4' \(file templates[/\\]comments.thtml, line 8\) "
                r"was ignored, because it wasn't the last item on the line\.",
            )
        # Now test .po file contents
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()

            self.assertMsgId("Translatable literal #9a", po_contents)
            self.assertNotIn("ignored comment #1", po_contents)

            self.assertNotIn("Translators: ignored i18n comment #1", po_contents)
            self.assertMsgId("Translatable literal #9b", po_contents)

            self.assertNotIn("ignored i18n comment #2", po_contents)
            self.assertNotIn("ignored comment #2", po_contents)
            self.assertMsgId("Translatable literal #9c", po_contents)

            self.assertNotIn("ignored comment #3", po_contents)
            self.assertNotIn("ignored i18n comment #3", po_contents)
            self.assertMsgId("Translatable literal #9d", po_contents)

            self.assertNotIn("ignored comment #4", po_contents)
            self.assertMsgId("Translatable literal #9e", po_contents)
            self.assertNotIn("ignored comment #5", po_contents)

            self.assertNotIn("ignored i18n comment #4", po_contents)
            self.assertMsgId("Translatable literal #9f", po_contents)
            self.assertIn("#. Translators: valid i18n comment #5", po_contents)

            self.assertMsgId("Translatable literal #9g", po_contents)
            self.assertIn("#. Translators: valid i18n comment #6", po_contents)
            self.assertMsgId("Translatable literal #9h", po_contents)
            self.assertIn("#. Translators: valid i18n comment #7", po_contents)
            self.assertMsgId("Translatable literal #9i", po_contents)

            self.assertRegex(po_contents, r"#\..+Translators: valid i18n comment #8")
            self.assertRegex(po_contents, r"#\..+Translators: valid i18n comment #9")
            self.assertMsgId("Translatable literal #9j", po_contents)