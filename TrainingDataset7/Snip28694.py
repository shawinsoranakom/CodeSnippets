def test_init_subclass(self):
        saved_kwargs = {}

        class A(models.Model):
            def __init_subclass__(cls, **kwargs):
                super().__init_subclass__()
                saved_kwargs.update(kwargs)

        kwargs = {"x": 1, "y": 2, "z": 3}

        class B(A, **kwargs):
            pass

        self.assertEqual(saved_kwargs, kwargs)