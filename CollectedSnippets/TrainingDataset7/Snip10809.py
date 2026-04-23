def flatten(self):
        """
        Recursively yield this expression and all subexpressions, in
        depth-first order.
        """
        yield self
        for expr in self.get_source_expressions():
            if expr:
                if hasattr(expr, "flatten"):
                    yield from expr.flatten()
                else:
                    yield expr