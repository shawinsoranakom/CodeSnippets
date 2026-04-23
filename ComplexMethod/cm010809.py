def set(self, spec: pytree.TreeSpec) -> None:
        if not (self.spec is None or self.spec == spec):
            raise AssertionError(f"spec mismatch: existing={self.spec}, new={spec}")
        if spec is None:
            raise AssertionError("spec must not be None")
        self.spec: pytree.TreeSpec = spec
        if self.spec.type in {tuple, list} and all(
            child.is_leaf() for child in spec.children()
        ):
            self.is_simple = True
        if self.spec.is_leaf():
            self.is_really_simple = True