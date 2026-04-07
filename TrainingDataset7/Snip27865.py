def test_clearable(self):
        """
        FileField.save_form_data() will clear its instance attribute value if
        passed False.
        """
        d = Document(myfile="something.txt")
        self.assertEqual(d.myfile, "something.txt")
        field = d._meta.get_field("myfile")
        field.save_form_data(d, False)
        self.assertEqual(d.myfile, "")