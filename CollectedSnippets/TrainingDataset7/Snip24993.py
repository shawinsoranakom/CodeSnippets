def test_pot_charset_header_is_utf8(self):
        """Content-Type: ... charset=CHARSET is replaced with charset=UTF-8"""
        msgs = (
            "# SOME DESCRIPTIVE TITLE.\n"
            "# (some lines truncated as they are not relevant)\n"
            '"Content-Type: text/plain; charset=CHARSET\\n"\n'
            '"Content-Transfer-Encoding: 8bit\\n"\n'
            "\n"
            "#: somefile.py:8\n"
            'msgid "mañana; charset=CHARSET"\n'
            'msgstr ""\n'
        )
        with tempfile.NamedTemporaryFile() as pot_file:
            pot_filename = pot_file.name
        write_pot_file(pot_filename, msgs)
        with open(pot_filename, encoding="utf-8") as fp:
            pot_contents = fp.read()
            self.assertIn("Content-Type: text/plain; charset=UTF-8", pot_contents)
            self.assertIn("mañana; charset=CHARSET", pot_contents)