def get_contents(self, origin):
        try:
            return self.templates_dict[origin.name]
        except KeyError:
            raise TemplateDoesNotExist(origin)