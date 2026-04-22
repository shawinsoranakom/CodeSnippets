def calling_cached_function(self, func: types.FunctionType) -> Iterator[None]:
        self._cached_func_stack.append(func)
        try:
            yield
        finally:
            self._cached_func_stack.pop()