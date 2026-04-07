def test_lazy_regular_method(self):
        original_object = 15
        lazy_obj = lazy(lambda: original_object, int)
        self.assertEqual(original_object.bit_length(), lazy_obj().bit_length())