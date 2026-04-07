def resolve_expression(self, obj, context):
        # This method is called for each object in self.target. See regroup()
        # for the reason why we temporarily put the object in the context.
        context[self.var_name] = obj
        return self.expression.resolve(context, ignore_failures=True)