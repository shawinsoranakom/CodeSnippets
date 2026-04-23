def is_complete(self) -> bool:
        """
        Whether the tensor completely overlaps with its underlying storage
        """
        if self.is_fake:
            # Theoretically, fake tensors should not appear in weights
            # But we handle this corner case to make it always complete
            return True
        if not self.is_contiguous:
            return False

        if self.storage_ptr is None:
            raise AssertionError("storage_ptr cannot be None for complete check")
        if self.storage_size is None:
            raise AssertionError("storage_size cannot be None for complete check")
        if self.start is None:
            raise AssertionError("start cannot be None for complete check")
        if self.end is None:
            raise AssertionError("end cannot be None for complete check")
        return (
            self.start == self.storage_ptr
            and self.end == self.storage_ptr + self.storage_size
        )