def test_model(self):
        """
        Passing a model to resolve_url() results in get_absolute_url() being
        called on that model instance.
        """
        m = UnimportantThing(importance=1)
        self.assertEqual(m.get_absolute_url(), resolve_url(m))