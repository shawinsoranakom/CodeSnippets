def test_none_in_generator(self):
        def gen():
            yield None

        with self.assertRaisesMessage(TypeError, self.cannot_encode_none_msg):
            urlencode({"a": gen()}, doseq=True)