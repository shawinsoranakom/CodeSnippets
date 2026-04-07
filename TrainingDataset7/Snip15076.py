def test_insert_get_absolute_url(self):
        """
        ABSOLUTE_URL_OVERRIDES should work even if the model doesn't have a
        get_absolute_url() method.
        """
        with self.settings(
            ABSOLUTE_URL_OVERRIDES={
                "absolute_url_overrides.testc": lambda o: "/test-c/%s/" % o.pk,
            },
        ):
            TestC = self._create_model_class("TestC")
            obj = TestC(pk=1, name="Foo")
            self.assertEqual("/test-c/%s/" % obj.pk, obj.get_absolute_url())