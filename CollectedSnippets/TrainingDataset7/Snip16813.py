def test_many_to_many(self):
        self.assertFormfield(Band, "members", forms.SelectMultiple)