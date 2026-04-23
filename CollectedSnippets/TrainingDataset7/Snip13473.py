def find_template(self, template_name, context):
        """
        This is a wrapper around engine.find_template(). A history is kept in
        the render_context attribute between successive extends calls and
        passed as the skip argument. This enables extends to work recursively
        without extending the same template twice.
        """
        history = context.render_context.setdefault(
            self.context_key,
            [self.origin],
        )
        template, origin = context.template.engine.find_template(
            template_name,
            skip=history,
        )
        history.append(origin)
        return template