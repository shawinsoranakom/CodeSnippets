def test_booleanfieldlistfilter_choices(self):
        modeladmin = BookAdmin(Book, site)
        self.verify_booleanfieldlistfilter_choices(modeladmin)