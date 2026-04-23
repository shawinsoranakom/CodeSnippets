def shuffle(self, *args: Any, seed: Any = None) -> MutableSequence[Any]:
        """Shuffle a list, either with a seed or without."""
        if not args:
            raise TypeError("shuffle expected at least 1 argument, got 0")

        # If first argument is iterable and more than 1 argument provided
        # but not a named seed, then use 2nd argument as seed.
        if isinstance(args[0], Iterable) and not isinstance(args[0], str):
            items = list(args[0])
            if len(args) > 1 and seed is None:
                seed = args[1]
        elif len(args) == 1:
            raise TypeError(f"'{type(args[0]).__name__}' object is not iterable")
        else:
            items = list(args)

        if seed:
            r = random.Random(seed)
            r.shuffle(items)
        else:
            random.shuffle(items)
        return items