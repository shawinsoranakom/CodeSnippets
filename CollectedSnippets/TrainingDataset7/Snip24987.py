def test_template_message_context_extractor(self):
        """
        Message contexts are correctly extracted for the {% translate %} and
        {% blocktranslate %} template tags (#14806).
        """
        management.call_command("makemessages", locale=[LOCALE], verbosity=0)
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()
            # {% translate %}
            self.assertIn('msgctxt "Special trans context #1"', po_contents)
            self.assertMsgId("Translatable literal #7a", po_contents)
            self.assertIn('msgctxt "Special trans context #2"', po_contents)
            self.assertMsgId("Translatable literal #7b", po_contents)
            self.assertIn('msgctxt "Special trans context #3"', po_contents)
            self.assertMsgId("Translatable literal #7c", po_contents)

            # {% translate %} with a filter
            for (
                minor_part
            ) in "abcdefgh":  # Iterate from #7.1a to #7.1h template markers
                self.assertIn(
                    'msgctxt "context #7.1{}"'.format(minor_part), po_contents
                )
                self.assertMsgId(
                    "Translatable literal #7.1{}".format(minor_part), po_contents
                )

            # {% blocktranslate %}
            self.assertIn('msgctxt "Special blocktranslate context #1"', po_contents)
            self.assertMsgId("Translatable literal #8a", po_contents)
            self.assertIn('msgctxt "Special blocktranslate context #2"', po_contents)
            self.assertMsgId("Translatable literal #8b-singular", po_contents)
            self.assertIn("Translatable literal #8b-plural", po_contents)
            self.assertIn('msgctxt "Special blocktranslate context #3"', po_contents)
            self.assertMsgId("Translatable literal #8c-singular", po_contents)
            self.assertIn("Translatable literal #8c-plural", po_contents)
            self.assertIn('msgctxt "Special blocktranslate context #4"', po_contents)
            self.assertMsgId("Translatable literal #8d %(a)s", po_contents)

            # {% trans %} and {% blocktrans %}
            self.assertMsgId("trans text", po_contents)
            self.assertMsgId("blocktrans text", po_contents)