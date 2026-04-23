def add(self, signature: tuple[type, ...], func: Callable[..., object]) -> None:
        """Add new types/method pair to dispatcher
        >>> # xdoctest: +SKIP
        >>> D = Dispatcher("add")
        >>> D.add((int, int), lambda x, y: x + y)
        >>> D.add((float, float), lambda x, y: x + y)
        >>> D(1, 2)
        3
        >>> D(1, 2.0)
        Traceback (most recent call last):
        ...
        NotImplementedError: Could not find signature for add: <int, float>
        >>> # When ``add`` detects a warning it calls the ``on_ambiguity`` callback
        >>> # with a dispatcher/itself, and a set of ambiguous type signature pairs
        >>> # as inputs.  See ``ambiguity_warn`` for an example.
        """
        # Handle annotations
        if not signature:
            annotations = self.get_func_annotations(func)
            if annotations:
                signature = annotations

        # Handle union types
        if any(isinstance(typ, tuple) for typ in signature):
            for typs in expand_tuples(signature):
                self.add(typs, func)
            return

        new_signature = []

        for index, typ in enumerate(signature, start=1):
            if not isinstance(typ, (type, list)):
                str_sig = ", ".join(
                    c.__name__ if isinstance(c, type) else str(c) for c in signature
                )
                raise TypeError(
                    f"Tried to dispatch on non-type: {typ}\n"
                    f"In signature: <{str_sig}>\n"
                    f"In function: {self.name}"
                )

            # handle variadic signatures
            if isinstance(typ, list):
                if index != len(signature):
                    raise TypeError("Variadic signature must be the last element")

                if len(typ) != 1:
                    raise TypeError(
                        "Variadic signature must contain exactly one element. "
                        "To use a variadic union type place the desired types "
                        "inside of a tuple, e.g., [(int, str)]"
                    )
                # pyrefly: ignore [bad-specialization]
                new_signature.append(Variadic[typ[0]])
            else:
                new_signature.append(typ)  # pyrefly: ignore[bad-argument-type]

        self.funcs[tuple(new_signature)] = func
        self._cache.clear()

        try:
            del self._ordering
        except AttributeError:
            pass