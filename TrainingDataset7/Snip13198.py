def compile_filter(self, token):
        """
        Convenient wrapper for FilterExpression
        """
        return FilterExpression(token, self)