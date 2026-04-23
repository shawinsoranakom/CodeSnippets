def validate_no_atomic_block(self):
        """Raise an error if an atomic block is active."""
        if self.in_atomic_block:
            raise TransactionManagementError(
                "This is forbidden when an 'atomic' block is active."
            )