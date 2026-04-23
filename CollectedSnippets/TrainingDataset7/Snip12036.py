def _not_support_combined_queries(self, operation_name):
        if self.query.combinator:
            raise NotSupportedError(
                "Calling QuerySet.%s() after %s() is not supported."
                % (operation_name, self.query.combinator)
            )