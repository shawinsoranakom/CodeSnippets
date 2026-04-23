def test_autodiscover_modules_found_but_bad_module(self):
        with self.assertRaisesMessage(
            ImportError, "No module named 'a_package_name_that_does_not_exist'"
        ):
            autodiscover_modules("bad_module")