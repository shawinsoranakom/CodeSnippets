def import_module(self, module_path):
        if module_path == serializers.BUILTIN_SERIALIZERS["yaml"]:
            raise ImportError(YAML_IMPORT_ERROR_MESSAGE)

        return self._import_module(module_path)