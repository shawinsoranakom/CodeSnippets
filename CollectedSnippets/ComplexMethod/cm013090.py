def __call__(
        self,
        model: torch.nn.Module,
        store_n_calls: int = 3,
        method_name: str = "forward",
    ):
        """Starts collecting inputs and outputs of a specific method.
        The model method is replaced by a new one collecting tensors
        before and after the inner one is called.
        The original method is restored after the collection.

        Args:
            model: Model
            store_n_calls: The collection stops after this many calls
                to avoid taking too much memory.
            method_name: Method name to spy on.
        """
        if not hasattr(model, method_name):
            raise ValueError(
                f"Model type {model} does not have a method {method_name!r}."
            )
        captured_method = getattr(model, method_name)
        sig = inspect.signature(captured_method)
        if self.info is None:
            kwargs_names = [
                p
                for p in sig.parameters
                if sig.parameters[p].kind == inspect.Parameter.VAR_KEYWORD
            ]
            args_names = [
                (p, i)
                for (i, p) in enumerate(sig.parameters)
                if sig.parameters[p].kind == inspect.Parameter.VAR_POSITIONAL
            ]
            self.info = InputObserverInfo(
                signature_names=list(sig.parameters),
                default_values={
                    p.name: p.default
                    for p in sig.parameters.values()
                    if p.default != inspect.Parameter.empty
                    and isinstance(p.default, (int, bool, str, float))
                },
                value_if_missing=self.value_if_missing,
                args_name_and_position=args_names[0] if args_names else None,
                kwargs_name=kwargs_names[0] if kwargs_names else None,
            )
        n_already_stored = len(self.info)
        lambda_method = lambda *args, _cm=captured_method, _snc=(  # noqa: E731
            store_n_calls + n_already_stored
        ), **kwargs: self._replaced_method(
            *args, _captured_method=_cm, _store_n_calls=_snc, **kwargs
        )

        # It may happen that the signature of the forward is used to trigger a preprocessing.
        # This is used in GenerationMixin (transformers):
        #   position_ids_key = "decoder_position_ids" if ... else "position_ids"
        #   if position_ids_key in set(inspect.signature(self.forward).parameters.keys()):
        lambda_method.__signature__ = sig  # type: ignore[attr-defined]

        setattr(model, method_name, lambda_method)

        try:
            yield self
        finally:
            setattr(model, method_name, captured_method)