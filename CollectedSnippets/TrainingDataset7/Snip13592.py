def url(self, context):
        path = self.path.resolve(context)
        return self.handle_simple(path)