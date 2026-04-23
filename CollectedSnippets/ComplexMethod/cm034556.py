def assertEqualReasoning(self, first, second, msg=None):
        if isinstance(first, Reasoning) and isinstance(second, Reasoning):
            if first.status != second.status or first.is_thinking != second.is_thinking or first.token != second.token or first.label != second.label:
                raise self.failureException(msg or f"{first.label} != {second.label}")
        elif first != second:
            raise self.failureException(msg or f"{first} != {second}")