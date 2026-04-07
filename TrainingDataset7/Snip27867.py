def test_changed(self):
        """
        FileField.save_form_data(), if passed a truthy value, updates its
        instance attribute.
        """
        d = Document(myfile="something.txt")
        self.assertEqual(d.myfile, "something.txt")
        field = d._meta.get_field("myfile")
        field.save_form_data(d, "else.txt")
        self.assertEqual(d.myfile, "else.txt")