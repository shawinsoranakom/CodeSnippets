def failed(self) -> bool:
        if self._failed is None and self.rc is not None and self.rc != 0:
            return True

        if self.failed_when_result is not None:
            return bool(self.failed_when_result)

        if self.loop_results and any(loop_result.failed_when_result is not None for loop_result in self.loop_results):
            return any(loop_result.failed_when_result for loop_result in self.loop_results)

        if self._failed is not None or self.loop_results is None:
            return bool(self._failed)

        return any(loop_result.failed for loop_result in self.loop_results)