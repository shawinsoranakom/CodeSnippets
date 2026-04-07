def setUp(self):
        super().setUp()
        copytree("canned_locale", "locale")
        self._set_times_for_all_po_files()