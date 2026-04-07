def test_validate_registry_resets_after_missing_module(self):
        from .test_module import site

        autodiscover_modules(
            "does_not_exist", "another_good_module", "does_not_exist2", register_to=site
        )
        self.assertEqual(site._registry, {"lorem": "ipsum"})