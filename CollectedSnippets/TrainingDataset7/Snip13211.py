def render_annotated(self, context):
        """
        Render the node. If debug is True and an exception occurs during
        rendering, the exception is annotated with contextual line information
        where it occurred in the template. For internal usage this method is
        preferred over using the render method directly.
        """
        try:
            return self.render(context)
        except Exception as e:
            if context.template.engine.debug:
                # Store the actual node that caused the exception.
                if not hasattr(e, "_culprit_node"):
                    e._culprit_node = self
                if (
                    not hasattr(e, "template_debug")
                    and context.render_context.template.origin == e._culprit_node.origin
                ):
                    e.template_debug = (
                        context.render_context.template.get_exception_info(
                            e,
                            e._culprit_node.token,
                        )
                    )
            raise