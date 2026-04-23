def eval(self, context):
            try:
                return func(context, self.first)
            except Exception:
                return False