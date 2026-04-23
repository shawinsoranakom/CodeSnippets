def render(self, context):
        obj_list = self.target.resolve(context, ignore_failures=True)
        if obj_list is None:
            # target variable wasn't found in context; fail silently.
            context[self.var_name] = []
            return ""
        # List of dictionaries in the format:
        # {'grouper': 'key', 'list': [list of contents]}.
        context[self.var_name] = [
            GroupedResult(grouper=key, list=list(val))
            for key, val in groupby(
                obj_list, lambda obj: self.resolve_expression(obj, context)
            )
        ]
        return ""