def get_existing_storage(self):
        return self.get_storage(
            [
                Message(constants.INFO, "Test message 1"),
                Message(constants.INFO, "Test message 2", extra_tags="tag"),
            ]
        )