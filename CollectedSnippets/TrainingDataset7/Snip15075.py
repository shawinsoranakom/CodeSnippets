def test_override_get_absolute_url(self):
        """
        ABSOLUTE_URL_OVERRIDES should override get_absolute_url().
        """

        def get_absolute_url(o):
            return "/test-b/%s/" % o.pk

        with self.settings(
            ABSOLUTE_URL_OVERRIDES={
                "absolute_url_overrides.testb": lambda o: "/overridden-test-b/%s/"
                % o.pk,
            },
        ):
            TestB = self._create_model_class("TestB", get_absolute_url)
            obj = TestB(pk=1, name="Foo")
            self.assertEqual("/overridden-test-b/%s/" % obj.pk, obj.get_absolute_url())