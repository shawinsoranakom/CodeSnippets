def eval(self, context):
        return self.value.resolve(context, ignore_failures=True)