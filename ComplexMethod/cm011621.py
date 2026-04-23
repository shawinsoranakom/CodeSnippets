def _out_wrapper(fn: Callable[_P, _T]) -> Callable[_P, _T]:
        """
        Adds the out parameter to a Python reference.
        """
        out_type = (
            TensorLikeType
            if is_tensor
            else GenericAlias(
                tuple, tuple(TensorLikeType for _ in range(len(out_names)))
            )
        )
        # For backward compatibility - should be able to remove once PEP585
        # conversion is complete.
        bc_out_type = (
            TensorLikeType
            if is_tensor
            else types.GenericAlias(
                tuple, tuple(TensorLikeType for _ in range(len(out_names)))
            )
        )
        return_type = (
            TensorLikeType
            if is_tensor
            else NamedTuple(
                f"return_types_{fn.__name__}",
                # pyrefly: ignore [bad-argument-count]
                [(o, TensorLikeType) for o in out_names],
            )
        )

        sig = inspect.signature(fn)
        factory_kwargs = ("device", "dtype")
        is_factory_fn = all(p in sig.parameters for p in factory_kwargs)

        @wraps(fn)
        def _fn(*args: _P.args, **kwargs: _P.kwargs):
            out = kwargs.pop("out", None)
            if is_factory_fn and out is not None:
                for k in factory_kwargs:
                    out_attr = getattr(out, k)
                    if k not in kwargs:
                        kwargs[k] = out_attr

            def maybe_check_copy_devices(out):
                if isinstance(out, TensorLike) and isinstance(args[0], TensorLike):
                    check_copy_devices(copy_from=args[0], copy_to=out)

            if isinstance(out, (tuple, list)):
                for o in out:
                    maybe_check_copy_devices(o)
            else:
                maybe_check_copy_devices(out)

            if pass_is_out:
                result = fn(*args, is_out=(out is not None), **kwargs)  # type: ignore[arg-type]
            else:
                result = fn(*args, **kwargs)
            if result is NotImplemented:
                return NotImplemented
            if not (
                (isinstance(result, TensorLike) and is_tensor)
                or (
                    isinstance(result, tuple)  # type: ignore[arg-type]
                    and len(result) == len(out_names)  # type: ignore[arg-type]
                )
                or (
                    fn.__name__ == "unbind" and isinstance(result, (list, tuple))  # type: ignore[arg-type]
                )
            ):
                raise AssertionError(
                    f"Unexpected result type: {type(result)}, is_tensor={is_tensor}, "
                    f"out_names={out_names}"
                )
            # unbind_copy is a special case: see https://github.com/pytorch/pytorch/issues/130829
            if out is not None:
                # Naively you might expect this assert to be true, but
                # it's not:
                #
                #   assert type(out) is type(result)
                #
                # The reason is that functions under this wrapper can
                # get registered to the Meta dispatch key, and that
                # means they can be executed in a context where tensor
                # subclasses are disabled (with no_dispatch), which is a
                # handy way for an is-a tensor subclass (e.g.,
                # FakeTensor) to have the normal meta backend create a
                # meta tensor, to be wrapped once it gets returned.
                # In this situation, you will get a FakeTensor as
                # the output tensor, but not the result--which will
                # be a normal meta tensor, but this is perfectly
                # harmless.
                if is_tensor and fn.__name__ != "unbind":
                    if not isinstance(out, TensorLike):
                        raise AssertionError(
                            f"out must be TensorLike, got {type(out)}"
                        )  # mypy
                    # These two operations are done in-place
                    _maybe_resize_out(
                        out,
                        result.shape,  # type: ignore[union-attr]
                        maybe_compute_memory_format(result),
                    )
                    _safe_copy_out(
                        copy_from=result,  # type: ignore[arg-type]
                        copy_to=out,
                        exact_dtype=exact_dtype,
                    )
                else:
                    if fn.__name__ != "unbind":
                        if not isinstance(out, tuple):
                            raise AssertionError(f"out must be tuple, got {type(out)}")  # type: ignore[arg-type]  # mypy
                    else:
                        if not isinstance(out, (list, tuple)):
                            raise AssertionError(
                                f"out must be list or tuple, got {type(out)}"
                            )  # type: ignore[arg-type]  # mypy
                    torch._check_type(
                        len(out) == len(result),  # type: ignore[arg-type]
                        lambda: f"expected tuple of {len(result)} elements but got {len(out)}",  # type: ignore[arg-type]
                    )
                    for r, o in zip(result, out):  # type: ignore[arg-type]
                        # These two operations are done in-place
                        _maybe_resize_out(o, r.shape, maybe_compute_memory_format(r))
                        _safe_copy_out(copy_from=r, copy_to=o, exact_dtype=exact_dtype)  # type: ignore[arg-type]
            else:
                out = result
            # mypy does not see through  the definition of out_type given that it's in a different scope
            return out if is_tensor else return_type(*out)  # type: ignore[operator]

        out_param = inspect.Parameter(
            "out",
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=None,
            annotation=out_type,
        )
        # Mark that the function now returns a tuple
        if not (
            isinstance(sig.return_annotation, (str, TypeVar))
            or sig.return_annotation in (sig.empty, out_type, bc_out_type)
        ):
            raise AssertionError(
                f"Unexpected return annotation: {sig.return_annotation}, "
                f"expected str, TypeVar, empty, {out_type}, or {bc_out_type}"
            )
        params = *sig.parameters.values(), out_param

        # If there's a Parameter.VAR_KEYWORD parameter (like **kwds), it must appear
        # after the out= parameter, which is Parameter.KEYWORD_ONLY. Sorting by
        # Parameter.kind guarantees that all the parameters are in legal order.
        params = sorted(params, key=lambda p: p.kind)

        _fn.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
            parameters=params,
            return_annotation=return_type,  # type: ignore[arg-type]
        )

        _fn.__annotations__ = dict(getattr(fn, "__annotations__", {}))
        _fn.__annotations__["out"] = out_type
        _fn.__annotations__["return"] = return_type

        # In the special case of having a single tensor out parameter with a
        # name other than out, add a special annotation to name the parameter
        if is_tensor and out_names != default_out_names:
            _fn.__annotations__[CustomOutParamAnnotation] = out_names[0]

        # Add an indicator attribute that can be used in special cases
        # where having a function wrapped by `out_wrapper` is not desirable e.g.
        # jit
        _fn._torch_decompositions_out_wrapper = (  # type: ignore[attr-defined]
            f"This function is wrapped by {out_wrapper.__module__}.out_wrapper"
        )

        return _fn