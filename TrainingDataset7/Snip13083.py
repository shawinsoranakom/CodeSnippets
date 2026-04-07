def get_result(self, result_id):
        # Results are only scoped to the current thread, hence
        # supports_get_result is False.
        try:
            return next(result for result in self.results if result.id == result_id)
        except StopIteration:
            raise TaskResultDoesNotExist(result_id) from None