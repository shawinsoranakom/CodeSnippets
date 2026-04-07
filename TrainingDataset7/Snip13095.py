def get_result(self, result_id):
        """
        Retrieve a task result by id.

        Raise TaskResultDoesNotExist if such result does not exist, or raise
        TaskResultMismatch if the result exists but belongs to another Task.
        """
        result = self.get_backend().get_result(result_id)
        if result.task.func != self.func:
            raise TaskResultMismatch(
                f"Task does not match (received {result.task.module_path!r})"
            )
        return result