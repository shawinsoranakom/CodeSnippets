def test_autodiscover_modules_several_found_with_registry(self):
        from .test_module import site

        autodiscover_modules("good_module", "another_good_module", register_to=site)
        self.assertEqual(site._registry, {"lorem": "ipsum"})