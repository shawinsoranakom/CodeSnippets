def test_slicing_of_f_expressions_with_slice_stop_less_than_slice_start(self):
        msg = "Slice stop must be greater than slice start."
        with self.assertRaisesMessage(ValueError, msg):
            F("name")[4:2]