def test_null(self):
        # null isn't well defined for a ManyToManyField, but changing it to
        # True causes backwards compatibility problems (#25320).
        self.assertFalse(AllFieldsModel._meta.get_field("m2m").null)
        self.assertTrue(AllFieldsModel._meta.get_field("reverse2").null)