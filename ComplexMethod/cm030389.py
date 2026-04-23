def reset_mock(self, visited=None, *,
                   return_value: bool = False,
                   side_effect: bool = False):
        "Restore the mock object to its initial state."
        if visited is None:
            visited = []
        if id(self) in visited:
            return
        visited.append(id(self))

        self.called = False
        self.call_args = None
        self.call_count = 0
        self.mock_calls = _CallList()
        self.call_args_list = _CallList()
        self.method_calls = _CallList()

        if return_value:
            self._mock_return_value = DEFAULT
        if side_effect:
            self._mock_side_effect = None

        for child in self._mock_children.values():
            if isinstance(child, _SpecState) or child is _deleted:
                continue
            child.reset_mock(visited, return_value=return_value, side_effect=side_effect)

        ret = self._mock_return_value
        if _is_instance_mock(ret) and ret is not self:
            ret.reset_mock(visited)