def test_validate_registry_keeps_intact(self):
        from .test_module import site

        with self.assertRaisesMessage(Exception, "Some random exception."):
            autodiscover_modules("another_bad_module", register_to=site)
        self.assertEqual(site._registry, {})