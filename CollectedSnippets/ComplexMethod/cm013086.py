def add_inputs(self, args: tuple[Any, ...], kwargs: dict[str, Any]):
        """Stores one set of inputs. They are deepcopied.

        Args:
            args: Positional arguments.
            kwargs: Named arguments.
        """
        cst_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k in self.signature_names
            and isinstance(v, (int, float, bool, str))
            and v != self.default_values.get(k, None)
            and self.default_values.get(k, None) is not None
        }
        kwargs = {
            k: v
            for k, v in kwargs.items()
            if v is not None and not isinstance(v, (int, float, bool, str))
        }

        # adds value_if_missing attributes
        for k, v in self.value_if_missing.items():
            if isinstance(k, str):
                if k not in kwargs:
                    # Validate that `value_if_missing` keys are compatible
                    # with the observed signature.
                    # If the function does not accept **kwargs,
                    # all value_if_missing keys must be
                    # present in the observed signature names.
                    if k not in self.signature_names and not self.kwargs_name:
                        raise ValueError(
                            f"Unexpected keyword argument {k!r} "
                            f"provided as a value_if_missing input "
                            "for a function that does not accept it. "
                            f"All value_if_missing keys must "
                            f"be in the observed signature: {tuple(self.signature_names)}."
                        )
                    kwargs[k] = v
            elif isinstance(k, int):
                if k >= len(self.signature_names):
                    raise ValueError(
                        f"Unexpected keyword argument {k=} "
                        f"provided as a value_if_missing input "
                        "for a function that does not accept it. "
                        f"All value_if_missing indices must "
                        f"be in the observed signature: {tuple(self.signature_names)}."
                    )
                if k >= len(args):
                    raise NotImplementedError(
                        f"Unexpected keyword argument {k=} "
                        f"provided as a value_if_missing input "
                        "for a function that does not accept it. "
                        f"All value_if_missing indices must "
                        f"be in the observed signature: {tuple(self.signature_names)}, "
                        f"only {len(args)} were given."
                    )
                list_args = list(args)
                list_args[k] = v
                args = tuple(list_args)
            else:
                raise TypeError(
                    f"Unexpected type {type(k)} for a missing value. The key is {k!r}."
                )

        # kwargs may come in a different order each time.
        # dictionaries are ordered and torch.export.export expects
        # dynamic shapes and kwargs to follow the same order.

        ordered_kwargs = {k: kwargs[k] for k in self.signature_names if k in kwargs}
        for k, v in kwargs.items():
            if k not in ordered_kwargs:
                ordered_kwargs[k] = v

        candidate = InputCandidate(
            args, ordered_kwargs, clone=True, cst_kwargs=cst_kwargs
        )
        self.inputs.append(candidate)
        if self._best_candidate is None or len(self._best_candidate) < len(candidate):
            self._best_candidate = candidate