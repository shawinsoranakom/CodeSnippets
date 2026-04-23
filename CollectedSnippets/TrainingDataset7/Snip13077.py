def get_result(self, result_id):
        """
        Retrieve a task result by id.

        Raise TaskResultDoesNotExist if such result does not exist.
        """
        raise NotImplementedError(
            "This backend does not support retrieving or refreshing results."
        )