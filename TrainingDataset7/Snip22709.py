def test_urlfield_unable_to_set_strip_kwarg(self):
        msg = "got multiple values for keyword argument 'strip'"
        with self.assertRaisesMessage(TypeError, msg):
            URLField(strip=False)