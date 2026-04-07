def test_override_plural_forms(self):
        """Ticket #20311."""
        management.call_command(
            "makemessages", locale=["es"], extensions=["djtpl"], verbosity=0
        )
        self.assertTrue(os.path.exists(self.PO_FILE_ES))
        with open(self.PO_FILE_ES, encoding="utf-8") as fp:
            po_contents = fp.read()
            found = re.findall(
                r'^(?P<value>"Plural-Forms.+?\\n")\s*$',
                po_contents,
                re.MULTILINE | re.DOTALL,
            )
            self.assertEqual(1, len(found))