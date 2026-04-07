def resolve_expression(self, *args, **kwargs):
        clone = self.clone()
        clone._resolve_node(clone, *args, **kwargs)
        clone.resolved = True
        return clone