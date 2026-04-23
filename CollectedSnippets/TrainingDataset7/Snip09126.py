def __eq__(self, other):
        return (
            isinstance(other, EmailValidator)
            and (set(self.domain_allowlist) == set(other.domain_allowlist))
            and (self.message == other.message)
            and (self.code == other.code)
        )