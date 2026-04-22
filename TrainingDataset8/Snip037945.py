def push(self, code, func=None):
        """Create a new frame, and save all of `code`'s vars into it."""

        self.frames.append(len(self.stack))

        for var in code.co_cellvars:
            self._set(var, var)

        if code.co_freevars:
            if func is not None:
                assert len(code.co_freevars) == len(func.__closure__)
                for var, cell in zip(code.co_freevars, func.__closure__):
                    self._set(var, cell.cell_contents)
            else:
                # List comprehension code objects also have freevars, but they
                # don't have a surrounding closure. In these cases we just use the name.
                for var in code.co_freevars:
                    self._set(var, var)