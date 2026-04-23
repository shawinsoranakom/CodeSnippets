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
            return out if is_tensor else return_type(*out)