def prefix(bp, func):
    """
    Create a prefix operator, given a binding power and a function that
    evaluates the node.
    """

    class Operator(TokenBase):
        lbp = bp

        def nud(self, parser):
            self.first = parser.expression(bp)
            self.second = None
            return self

        def eval(self, context):
            try:
                return func(context, self.first)
            except Exception:
                return False

    return Operator