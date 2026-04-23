def test_class_attributes(self):
        """
        The callable returned from as_view() has proper special attributes.
        """
        cls = SimpleView
        view = cls.as_view()
        self.assertEqual(view.__doc__, cls.__doc__)
        self.assertEqual(view.__name__, "view")
        self.assertEqual(view.__module__, cls.__module__)
        self.assertEqual(view.__qualname__, f"{cls.as_view.__qualname__}.<locals>.view")
        self.assertEqual(view.__annotations__, cls.dispatch.__annotations__)
        self.assertFalse(hasattr(view, "__wrapped__"))