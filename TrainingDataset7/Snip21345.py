def test_slicing_of_f_expressions_with_step(self):
        msg = "Step argument is not supported."
        with self.assertRaisesMessage(ValueError, msg):
            F("name")[::4]