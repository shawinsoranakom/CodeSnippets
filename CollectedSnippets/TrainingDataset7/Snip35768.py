def test_mixing_args_and_kwargs(self):
        msg = "Don't mix *args and **kwargs in call to reverse()!"
        with self.assertRaisesMessage(ValueError, msg):
            reverse("name", args=["a"], kwargs={"b": "c"})