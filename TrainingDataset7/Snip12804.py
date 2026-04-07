def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["optgroups"] = self.optgroups(
            name, context["widget"]["value"], attrs
        )
        return context