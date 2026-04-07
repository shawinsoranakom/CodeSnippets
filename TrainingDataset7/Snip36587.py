def test_validate_registry_resets_after_erroneous_module(self):
        from .test_module import site

        with self.assertRaisesMessage(Exception, "Some random exception."):
            autodiscover_modules(
                "another_good_module", "another_bad_module", register_to=site
            )
        self.assertEqual(site._registry, {"lorem": "ipsum"})