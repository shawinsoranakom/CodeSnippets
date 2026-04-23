def render(self, context):
        try:
            output = self.filter_expression.resolve(context)
        except UnicodeDecodeError:
            # Unicode conversion can fail sometimes for reasons out of our
            # control (e.g. exception rendering). In that case, we fail
            # quietly.
            return ""
        return render_value_in_context(output, context)