def get_template_libraries(self, libraries):
        loaded = {}
        for name, path in libraries.items():
            loaded[name] = import_library(path)
        return loaded