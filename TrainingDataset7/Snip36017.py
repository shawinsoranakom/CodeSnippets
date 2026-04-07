def test_is_django_module(self):
        for module, expected in ((zoneinfo, False), (sys, False), (autoreload, True)):
            with self.subTest(module=module):
                self.assertIs(autoreload.is_django_module(module), expected)