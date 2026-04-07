def test_context_in_single_quotes(self):
        management.call_command("makemessages", locale=[LOCALE], verbosity=0)
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE) as fp:
            po_contents = fp.read()
            # {% translate %}
            self.assertIn('msgctxt "Context wrapped in double quotes"', po_contents)
            self.assertIn('msgctxt "Context wrapped in single quotes"', po_contents)

            # {% blocktranslate %}
            self.assertIn(
                'msgctxt "Special blocktranslate context wrapped in double quotes"',
                po_contents,
            )
            self.assertIn(
                'msgctxt "Special blocktranslate context wrapped in single quotes"',
                po_contents,
            )