def super(self):
        if not hasattr(self, "context"):
            raise TemplateSyntaxError(
                "'%s' object has no attribute 'context'. Did you use "
                "{{ block.super }} in a base template?" % self.__class__.__name__
            )
        render_context = self.context.render_context
        if (
            BLOCK_CONTEXT_KEY in render_context
            and render_context[BLOCK_CONTEXT_KEY].get_block(self.name) is not None
        ):
            return mark_safe(self.render(self.context))
        return ""