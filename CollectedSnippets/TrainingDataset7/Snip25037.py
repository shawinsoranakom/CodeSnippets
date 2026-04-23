def setUp(self):
        super().setUp()
        po_file = Path(self.PO_FILE)
        po_file_tmp = Path(self.PO_FILE + ".tmp")
        if os.name == "nt":
            # msgmerge outputs Windows style paths on Windows.
            po_contents = po_file_tmp.read_text().replace(
                "#: __init__.py",
                "#: .\\__init__.py",
            )
            po_file.write_text(po_contents)
        else:
            po_file_tmp.rename(po_file)
        self.original_po_contents = po_file.read_text()