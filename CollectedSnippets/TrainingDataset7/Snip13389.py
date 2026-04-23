def render(self, context):
        try:
            return self.partial_mapping[self.partial_name].render(context)
        except KeyError:
            raise TemplateSyntaxError(
                f"Partial '{self.partial_name}' is not defined in the current template."
            )