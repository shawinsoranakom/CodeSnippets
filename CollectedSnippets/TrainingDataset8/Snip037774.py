def calling_cached_function(self) -> Iterator[None]:
        self._cached_message_stack.append([])
        self._seen_dg_stack.append(set())
        try:
            yield
        finally:
            self._most_recent_messages = self._cached_message_stack.pop()
            self._seen_dg_stack.pop()