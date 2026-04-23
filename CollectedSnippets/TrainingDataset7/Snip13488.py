def get_template_sources(self, template_name):
        for loader in self.loaders:
            yield from loader.get_template_sources(template_name)