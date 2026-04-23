def __init__(
        self,
        expr: object,
        shape_env: ShapeEnv | None,
        pytype: type,
        hint: HintType | object,
        constant: int | float | bool | None = None,
        fx_node: object = None,
        optimized_summation: bool = False,
    ) -> None:
        self._expr = expr
        self.shape_env = shape_env
        self.pytype = pytype
        self._optimized_summation = optimized_summation
        self._expr_ver = -1
        self._expr_cache = None

        # What's the difference between hint and constant?
        #
        # - A constant is known to be invariant across invocations of the model;
        #   it will always be this value.  We only really know this when we
        #   encounter an honest-to-goodness literal (when wrapping it into
        #   a SymNode, we set constant.)  Most of the time, constant is None
        #
        # - A hint is a *particular* value from the particular run we are
        #   tracing, but it may vary the next time around.  It's useful to
        #   keep this around, as if we need a concrete value from a SymNode,
        #   we will return the hint and guard on the expression that produced
        #   it giving the same hint next time around.  The hint is not
        #   guaranteed to be set either: if you have an unbacked SymNode,
        #   there won't be any hint; it was the result of some tensor-dependent
        #   computation, but we don't know what it actually is because we
        #   haven't actually run the tensor computation.
        #
        # If _hint is None, we will query maybe_evaluate_static(compute_hint=True)
        # in hopes that we've learned enough about the unbacked symints to
        # discharge the hint; otherwise, you're likely to just error out.
        #
        # (A previous version of this system had some optimizations to only
        # recompute when it was possible we had learned enough about the
        # unbacked symint that a hint was now possible, but as we added more
        # potential refinements to unbacked symints this got harder to keep
        # in sync, so we've deleted it for now.)

        def compute_hint() -> HintType | SymInt | SymFloat | SymBool:
            from torch.fx.experimental.symbolic_shapes import has_free_unbacked_symbols

            # This occasionally gets exercised by, e.g.,
            # convert_shape_to_symint.  It's just a nicety so you don't HAVE
            # to have a correct hint on hand when making a SymNode.
            # Don't attempt to compute for unbacked, this can be quite
            # expensive.
            if has_free_unbacked_symbols(self.expr):
                return None
            if self.shape_env is None:
                raise RuntimeError("shape_env is required to compute hint")
            hint = self.shape_env._maybe_evaluate_static(self.expr, compute_hint=True)
            if hint is not None:
                hint = self.pytype(hint) if not isinstance(hint, SymTypes) else hint
            return hint

        if hint is _NO_HINT:
            # Caller explicitly indicates hint is unavailable, don't compute
            hint = None
        elif hint is not None:
            if not (type(hint) is pytype or type(hint) is _to_symtype(pytype)):
                raise AssertionError(
                    "Cannot create SymNode of type "
                    f"{pytype} with incompatible hint of type {type(hint)}"
                )
            if self.shape_env and self.shape_env._translation_validation_enabled:
                # This is technically not TV, but this assert is expensive so
                # let's only do it when we're already doing expensive things
                computed_hint = compute_hint()
                if hint != computed_hint:
                    raise AssertionError(f"{hint} != {computed_hint} (for {self.expr})")
        else:
            hint = compute_hint()
        self._hint = hint
        self.constant: int | float | bool | None = constant

        # Record the FX node of the current node if we are doing translation
        # validation. They will be used for building the input assertions for
        # the translation validation problem.
        tx_validation_en = (
            self.shape_env and self.shape_env._translation_validation_enabled
        )
        self.fx_node = tx_validation_en and fx_node