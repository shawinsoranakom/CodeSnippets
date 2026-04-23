def test_slicing_of_f_unsupported_field(self):
        msg = "This field does not support slicing."
        with self.assertRaisesMessage(NotSupportedError, msg):
            Company.objects.update(num_chairs=F("num_chairs")[:4])