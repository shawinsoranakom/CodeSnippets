def test_get_absolute_url(self):
        """
        get_absolute_url() functions as a normal method.
        """

        def get_absolute_url(o):
            return "/test-a/%s/" % o.pk

        TestA = self._create_model_class("TestA", get_absolute_url)

        self.assertTrue(hasattr(TestA, "get_absolute_url"))
        obj = TestA(pk=1, name="Foo")
        self.assertEqual("/test-a/%s/" % obj.pk, obj.get_absolute_url())