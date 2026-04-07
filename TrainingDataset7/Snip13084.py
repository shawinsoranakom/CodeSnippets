async def aget_result(self, result_id):
        try:
            return next(result for result in self.results if result.id == result_id)
        except StopIteration:
            raise TaskResultDoesNotExist(result_id) from None