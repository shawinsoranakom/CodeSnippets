def render(self, context):
        self.count += 1
        for v in context.flatten().values():
            try:
                str(v)
            except AttributeError:
                pass
        return str(self.count)