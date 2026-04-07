def get_contents(self, origin):
        try:
            with open(origin.name, encoding=self.engine.file_charset) as fp:
                return fp.read()
        except FileNotFoundError:
            raise TemplateDoesNotExist(origin)