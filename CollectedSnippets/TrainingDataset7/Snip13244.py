def bind_template(self, template):
        if self.template is not None:
            raise RuntimeError("Context is already bound to a template")
        self.template = template
        try:
            yield
        finally:
            self.template = None