def return_value(self):
        """
        The return value of the task.

        If the task didn't succeed, an exception is raised.
        This is to distinguish against the task returning None.
        """
        if self.status == TaskResultStatus.SUCCESSFUL:
            return self._return_value
        elif self.status == TaskResultStatus.FAILED:
            raise ValueError("Task failed")
        else:
            raise ValueError("Task has not finished yet")