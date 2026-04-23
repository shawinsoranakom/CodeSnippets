def tearDownClass(cls):
        """Puts yaml back if necessary"""
        super().tearDownClass()

        importlib.import_module = cls._import_module_mock._import_module

        # clear out cached serializers to clean out BadSerializer instances
        serializers._serializers = {}