def __torch_dispatch__(
        self,
        func: OpOverload,
        types: Sequence[type],
        args: Sequence[object] = (),
        kwargs: Mapping[str, object] | None = None,
    ) -> object:
        kwargs = kwargs or {}

        fake_r = None
        fake_args: Sequence[object] = ()
        fake_kwargs: Mapping[str, object] = {}

        # empty_like excluded for now due to sparse complex
        # aten._to_dense.default this one is getting called with csc
        if (
            func
            not in (
                aten.lift_fresh.default,
                aten.lift_fresh_copy.default,
                aten.set_.source_Storage_storage_offset,
            )
            and not self.ignore_op_fn(func)
            and (
                not self.only_check_ops_with_meta
                or torch._subclasses.fake_impls.has_meta(func)
            )
            and torch.Tag.dynamic_output_shape not in func.tags
            and torch.Tag.inplace_view not in func.tags
            and torch.Tag.data_dependent_output not in func.tags
        ):
            # Do not import symbolic_shapes at the top of the module as it imports sympy and that's slow
            from torch.fx.experimental.symbolic_shapes import ShapeEnv

            try:
                # TODO: enable_python_dispatcher() here
                with FakeTensorMode(shape_env=ShapeEnv()) as fake_mode:
                    fake_args, fake_kwargs = pytree.tree_map_only(
                        torch.Tensor,
                        functools.partial(fake_mode.from_tensor, static_shapes=True),
                        (args, kwargs),
                    )
                    with warnings.catch_warnings():
                        fake_r = func(*fake_args, **fake_kwargs)
            except UnsupportedFakeTensorException:
                pass

        context = (
            f"When comparing the output of {func} on FakeTensor and concrete Tensors, "
            f"found"
        )
        r = func(*args, **kwargs)
        if fake_r is not None:
            r_flat = pytree.tree_leaves(r)
            f_flat = pytree.tree_leaves(fake_r)
            if len(f_flat) != len(r_flat):
                raise AssertionError(
                    f"{context} mismatch in number of returns {len(f_flat)} != {len(r_flat)}"
                )

            if self.check_aliasing:
                _check_alias_info(
                    context, r, (args, kwargs), fake_r, (fake_args, fake_kwargs)
                )

            for idx, (r_out, f_out) in enumerate(
                zip(pytree.tree_leaves(r), pytree.tree_leaves(fake_r))
            ):
                r_is_ten = isinstance(r_out, torch.Tensor)
                if r_is_ten != isinstance(f_out, torch.Tensor):
                    raise AssertionError(
                        f"{context} mismatched number of tensor outputs"
                    )
                if r_is_ten:
                    try:
                        _check_fake_real_tensors(
                            r_out,
                            f_out,
                            sizes=True,
                            strides=self.check_strides,
                            storage_offset=True,
                            requires_grad=True,
                        )
                    except Exception as e:
                        if is_sdpa_error(func, idx, e):
                            continue
                        error_message = (
                            f"{context} mismatched tensor metadata: {e}"
                            if len(r_flat) == 1
                            else f"{context} mismatched tensor metadata for output[{idx}]: {e}"
                        )
                        raise MetadataMismatchError(error_message) from e
        return r