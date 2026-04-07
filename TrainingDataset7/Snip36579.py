def tearDown(self):
        sys.path_importer_cache.clear()

        sys.modules.pop("utils_tests.test_module.another_bad_module", None)
        sys.modules.pop("utils_tests.test_module.another_good_module", None)
        sys.modules.pop("utils_tests.test_module.bad_module", None)
        sys.modules.pop("utils_tests.test_module.good_module", None)
        sys.modules.pop("utils_tests.test_module", None)