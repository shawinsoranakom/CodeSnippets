def tearDown(self):
        sys.path_importer_cache.clear()

        sys.modules.pop("egg_module.sub1.sub2.bad_module", None)
        sys.modules.pop("egg_module.sub1.sub2.good_module", None)
        sys.modules.pop("egg_module.sub1.sub2", None)
        sys.modules.pop("egg_module.sub1", None)
        sys.modules.pop("egg_module.bad_module", None)
        sys.modules.pop("egg_module.good_module", None)
        sys.modules.pop("egg_module", None)