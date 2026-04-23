def test_bad_callback(self):
        # A bad callback provided by user still gives an error
        with self.assertRaises(TypeError):
            modelform_factory(
                Person,
                fields="__all__",
                formfield_callback="not a function or callable",
            )