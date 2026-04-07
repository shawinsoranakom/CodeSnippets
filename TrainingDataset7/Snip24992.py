def test_po_file_encoding_when_updating(self):
        """
        Update of PO file doesn't corrupt it with non-UTF-8 encoding on Windows
        (#23271).
        """
        BR_PO_BASE = "locale/pt_BR/LC_MESSAGES/django"
        shutil.copyfile(BR_PO_BASE + ".pristine", BR_PO_BASE + ".po")
        management.call_command("makemessages", locale=["pt_BR"], verbosity=0)
        self.assertTrue(os.path.exists(BR_PO_BASE + ".po"))
        with open(BR_PO_BASE + ".po", encoding="utf-8") as fp:
            po_contents = fp.read()
            self.assertMsgStr("Größe", po_contents)