def _validate_salt_size(self, salt_size: int | None) -> int:
        if salt_size is not None and not isinstance(salt_size, int):
            raise TypeError('salt_size must be an integer')
        salt_size = salt_size or self.algo_data.salt_size
        if self.algo_data.salt_exact and salt_size != self.algo_data.salt_size:
            raise AnsibleError(f"invalid salt size supplied ({salt_size}), expected {self.algo_data.salt_size}")
        elif not self.algo_data.salt_exact and salt_size > self.algo_data.salt_size:
            raise AnsibleError(f"invalid salt size supplied ({salt_size}), expected at most {self.algo_data.salt_size}")
        return salt_size