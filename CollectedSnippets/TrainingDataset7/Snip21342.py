def test_slicing_of_f_expressions_with_negative_index(self):
        msg = "Negative indexing is not supported."
        indexes = [slice(0, -4), slice(-4, 0), slice(-4), -5]
        for i in indexes:
            with self.subTest(i=i), self.assertRaisesMessage(ValueError, msg):
                F("name")[i]