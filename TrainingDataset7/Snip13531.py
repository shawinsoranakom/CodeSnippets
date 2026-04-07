def eval(self, context):
            try:
                return func(context, self.first, self.second)
            except Exception:
                # Templates shouldn't throw exceptions when rendering. We are
                # most likely to get exceptions for things like:
                # {% if foo in bar %}
                # where 'bar' does not support 'in', so default to False.
                return False