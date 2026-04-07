def test_slicing_of_f_expressions_with_invalid_type(self):
        msg = "Argument to slice must be either int or slice instance."
        with self.assertRaisesMessage(TypeError, msg):
            F("name")["error"]