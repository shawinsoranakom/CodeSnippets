def test_booleanfieldlistfilter(self):
        modeladmin = BookAdmin(Book, site)
        self.verify_booleanfieldlistfilter(modeladmin)