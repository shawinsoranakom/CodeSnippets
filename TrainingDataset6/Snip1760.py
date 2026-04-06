def load_source(name, pathname, _file=None):
        module_spec = importlib.util.spec_from_file_location(name, pathname)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module