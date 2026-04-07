def test_comments_extractor(self):
        management.call_command("makemessages", locale=[LOCALE], verbosity=0)
        self.assertTrue(os.path.exists(self.PO_FILE))
        with open(self.PO_FILE, encoding="utf-8") as fp:
            po_contents = fp.read()
            self.assertNotIn("This comment should not be extracted", po_contents)

            # Comments in templates
            self.assertIn(
                "#. Translators: This comment should be extracted", po_contents
            )
            self.assertIn(
                "#. Translators: Django comment block for translators\n#. "
                "string's meaning unveiled",
                po_contents,
            )
            self.assertIn("#. Translators: One-line translator comment #1", po_contents)
            self.assertIn(
                "#. Translators: Two-line translator comment #1\n#. continued here.",
                po_contents,
            )
            self.assertIn("#. Translators: One-line translator comment #2", po_contents)
            self.assertIn(
                "#. Translators: Two-line translator comment #2\n#. continued here.",
                po_contents,
            )
            self.assertIn("#. Translators: One-line translator comment #3", po_contents)
            self.assertIn(
                "#. Translators: Two-line translator comment #3\n#. continued here.",
                po_contents,
            )
            self.assertIn("#. Translators: One-line translator comment #4", po_contents)
            self.assertIn(
                "#. Translators: Two-line translator comment #4\n#. continued here.",
                po_contents,
            )
            self.assertIn(
                "#. Translators: One-line translator comment #5 -- with "
                "non ASCII characters: áéíóúö",
                po_contents,
            )
            self.assertIn(
                "#. Translators: Two-line translator comment #5 -- with "
                "non ASCII characters: áéíóúö\n#. continued here.",
                po_contents,
            )