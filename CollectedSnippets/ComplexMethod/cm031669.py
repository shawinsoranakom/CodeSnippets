def memoize_wrapper(self: "Parser", *args: object) -> Any:
        mark = self._mark()
        key = mark, method_name, args
        # Fast path: cache hit, and not verbose.
        if key in self._cache and not self._verbose:
            tree, endmark = self._cache[key]
            self._reset(endmark)
            return tree
        # Slow path: no cache hit, or verbose.
        verbose = self._verbose
        argsr = ",".join(repr(arg) for arg in args)
        fill = "  " * self._level
        if key not in self._cache:
            if verbose:
                print(f"{fill}{method_name}({argsr}) ... (looking at {self.showpeek()})")
            self._level += 1
            tree = method(self, *args)
            self._level -= 1
            if verbose:
                print(f"{fill}... {method_name}({argsr}) -> {tree!s:.200}")
            endmark = self._mark()
            self._cache[key] = tree, endmark
        else:
            tree, endmark = self._cache[key]
            if verbose:
                print(f"{fill}{method_name}({argsr}) -> {tree!s:.200}")
            self._reset(endmark)
        return tree