def test_booleanfieldlistfilter_tuple(self):
        modeladmin = BookAdminWithTupleBooleanFilter(Book, site)
        self.verify_booleanfieldlistfilter(modeladmin)