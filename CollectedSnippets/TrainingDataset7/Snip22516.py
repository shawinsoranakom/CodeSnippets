def test_form_label_association(self):
        # label tag is correctly associated with first rendered dropdown
        a = GetDate({"mydate_month": "1", "mydate_day": "1", "mydate_year": "2010"})
        self.assertIn('<label for="id_mydate_day">', a.as_p())