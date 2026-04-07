def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if self.allow_multiple_selected:
            context["widget"]["attrs"]["multiple"] = True
        return context