def subwidgets(self, name, value, attrs=None):
        context = self.get_context(name, value, attrs)
        yield context["widget"]