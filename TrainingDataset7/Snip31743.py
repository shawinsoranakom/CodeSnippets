def setUpClass(cls):
        """Removes imported yaml and stubs importlib.import_module"""
        super().setUpClass()

        cls._import_module_mock = YamlImportModuleMock()
        importlib.import_module = cls._import_module_mock.import_module

        # clear out cached serializers to emulate yaml missing
        serializers._serializers = {}