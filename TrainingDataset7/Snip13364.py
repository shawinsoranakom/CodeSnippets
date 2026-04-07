def render(self, context):
        output = self.nodelist.render(context)
        # Apply filters.
        with context.push(var=output):
            return self.filter_expr.resolve(context)