def test_unchanged(self):
        """
        FileField.save_form_data() considers None to mean "no change" rather
        than "clear".
        """
        d = Document(myfile="something.txt")
        self.assertEqual(d.myfile, "something.txt")
        field = d._meta.get_field("myfile")
        field.save_form_data(d, None)
        self.assertEqual(d.myfile, "something.txt")