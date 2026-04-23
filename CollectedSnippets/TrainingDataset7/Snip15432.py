def test_booleanfieldlistfilter_tuple_choices(self):
        modeladmin = BookAdminWithTupleBooleanFilter(Book, site)
        self.verify_booleanfieldlistfilter_choices(modeladmin)