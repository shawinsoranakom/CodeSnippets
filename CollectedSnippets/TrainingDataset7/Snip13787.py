def suite_result(self, suite, result, **kwargs):
        return (
            len(result.failures) + len(result.errors) + len(result.unexpectedSuccesses)
        )