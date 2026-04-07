def template_context_processors(self):
        return [import_string(path) for path in self.context_processors]