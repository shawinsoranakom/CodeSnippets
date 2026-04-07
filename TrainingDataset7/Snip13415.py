def get_template_builtins(self, builtins):
        return [import_library(x) for x in builtins]