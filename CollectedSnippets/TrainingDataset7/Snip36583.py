def test_autodiscover_modules_several_one_bad_module(self):
        with self.assertRaisesMessage(
            ImportError, "No module named 'a_package_name_that_does_not_exist'"
        ):
            autodiscover_modules("good_module", "bad_module")