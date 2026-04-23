def __post_init__(self):
        if not self.placeholder:
            super().__post_init__()

        if self.become and self.become not in SUPPORTED_BECOME_METHODS:
            raise Exception(f'POSIX remote completion entry "{self.name}" setting "become" must be omitted or one of: {", ".join(SUPPORTED_BECOME_METHODS)}')

        if not self.supported_pythons:
            if self.version and not self.placeholder:
                raise Exception(f'POSIX remote completion entry "{self.name}" must provide a "python" setting.')
        else:
            if not self.version:
                raise Exception(f'POSIX remote completion entry "{self.name}" is a platform default and cannot provide a "python" setting.')