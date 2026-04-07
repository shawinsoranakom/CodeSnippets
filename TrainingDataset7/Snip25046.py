def setUp(self):
        super().setUp()
        with open(self.PO_FILE) as fp:
            self.po_contents = fp.read()