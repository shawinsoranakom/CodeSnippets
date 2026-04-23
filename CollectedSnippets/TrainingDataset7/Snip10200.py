def __replace__(self, /, **changes):
        args = [
            changes.pop(name, value)
            for name, value in zip(
                get_func_args(self.__class__),
                self._constructor_args[0],
            )
        ]
        return self.__class__(*args, **(self._constructor_args[1] | changes))