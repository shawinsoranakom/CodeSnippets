def empty_create_subclass(
            t: MetaTensorDesc[Any],
            outer_size: tuple[IntLikeType, ...],
            outer_stride: tuple[IntLikeType, ...],
            symbolic_context: torch.fx.experimental.symbolic_shapes.SymbolicContext
            | None = symbolic_context,
            source: torch._guards.Source | None = source,
        ) -> _TensorT:
            from torch.fx.experimental.symbolic_shapes import SubclassSymbolicContext

            if t.attrs is None:
                raise AssertionError("t.attrs must not be None for subclass")
            if t.type is None:
                raise AssertionError("t.type must not be None for subclass")
            # NB: t.ctx could be None if the subclass in question has no
            # meaningful context

            # Note: transform_subclass will use __tensor_unflatten__ to generate
            # a fresh subclass wrapper with outer sizes / strides according to the
            # outer symbolic context (passed in to this function). Inner size / stride
            # / storage offset symbols are allocated according to the appropriate inner
            # symbolic contexts, after which the checks in transform_subclass() will
            # relate them to the outer metadata as possible.
            #
            # Morally, the code here is same as transform_subclass, but we've
            # written it from scratch to read EmptyCreateSubclass
            outer_size = outer_size if outer_size is not None else t.size
            # pyrefly: ignore [bad-assignment]
            outer_stride = outer_stride if outer_stride is not None else t.stride

            if symbolic_context is not None and not isinstance(
                symbolic_context, SubclassSymbolicContext
            ):
                raise AssertionError(
                    f"Expected SubclassSymbolicContext or None, got {type(symbolic_context)}"
                )

            if source is None:
                raise AssertionError("source must not be None")
            sub = self._empty_create_subclass(
                t,
                # pyrefly: ignore[bad-argument-type]
                outer_size,
                # pyrefly: ignore[bad-argument-type]
                outer_stride,
                shape_env,
                symbolic_context,
                callback,
                source,
            )

            # NB: Purposefully guard here to simplify the inner / outer symbols.
            # Using sym_eq() for symbolic comparison can result in an expression that's too
            # difficult to guard on, so we use == here.
            if sub.shape != outer_size:
                raise AssertionError(
                    f"Expected return value from {t.type}__tensor_unflatten__() to have "
                    f"shape equal to {outer_size}, but got: {sub.shape}"
                )
            if sub.stride() != outer_stride:
                raise AssertionError(
                    f"Expected return value from {t.type}__tensor_unflatten__() to have "
                    f"stride equal to {outer_stride}, but got: {sub.stride()}"
                )

            return sub