def _maybe_infer_fake(
        self, func: OpOverload, path: KeyPath, fake: object, real: object
    ) -> tuple[object | None, bool]:
        """
        Helper to cross-check fake/real output properties & values,
        and create new fake vals if mismatched.
        Returns tuple of object & boolean, for whether or not it was overwrriten
        """
        import sympy

        from torch._subclasses.fake_utils import _check_fake_real_tensors

        def _check_fake_real_vals(fake: Any, real: Any) -> None:
            # use real values + ShapeEnv to check mismatches between potentially symbolic values
            if isinstance(fake, (SymInt, SymFloat)):
                # symbolic expression, ask ShapeEnv to substitute known backed/unbacked values
                if self.shape_env is None:
                    raise AssertionError(
                        "self.shape_env must not be None for symbolic values"
                    )
                if (
                    not fake.node.expr.free_symbols
                    - self.shape_env.backed_var_to_val.keys()
                    - self.shape_env.real_tensor_prop_unbacked_vals.keys()
                ):
                    if (
                        self.shape_env._maybe_evaluate_static(
                            sympy.Eq(fake.node.expr, real), compute_hint=True
                        )
                        is not sympy.S.true
                    ):
                        raise MetadataMismatchError(
                            f"mismatch between fake value {fake} and real value {real} "
                        )
            elif isinstance(
                fake, (int, float, bool)
            ):  # concrete value, check direct equality
                if fake != real:
                    raise MetadataMismatchError(
                        f"mismatch between fake value {fake} and real value {real} "
                    )

        if isinstance(fake, torch.Tensor):
            try:
                _check_fake_real_tensors(
                    real,  # type: ignore[arg-type]
                    fake,  # type: ignore[arg-type]
                    context="Real tensor propagation found",
                    sizes=False,  # manual check below
                    strides=False,  # skip strides
                    storage_offset=True,
                    requires_grad=False,  # issues with FakeTensorConverter preserving requires_grad
                )
            except MetadataMismatchError as exc:
                if torch._functorch.config.generate_fake_kernels_from_real_mismatches:
                    dtrace_structured(
                        "mismatched_fake_kernel",
                        metadata_fn=lambda: {
                            "op": str(func),
                            "reason": exc.reason,  # noqa: F821
                        },
                    )
                    return _infer_fake_from_real_tensor(self, func, real), True  # type: ignore[arg-type]
                raise MetadataMismatchError(
                    f"Real tensor propagation found a metadata mismatch between "
                    f"fake tensor {fake} and real tensor {real}, "
                    f" at output{keystr(path)}, for func: {func}"
                ) from exc

            for j, (s_fake, s_real) in enumerate(zip(fake.size(), real.size())):  # type: ignore[attr-defined]
                try:
                    _check_fake_real_vals(s_fake, s_real)
                except MetadataMismatchError as exc:
                    if torch._functorch.config.generate_fake_kernels_from_real_mismatches:
                        dtrace_structured(
                            "mismatched_fake_kernel",
                            metadata_fn=lambda: {
                                "op": str(func),
                                "reason": exc.reason,  # noqa: F821
                            },
                        )
                        return _infer_fake_from_real_tensor(self, func, real), True  # type: ignore[arg-type]
                    raise MetadataMismatchError(
                        f"Real tensor propagation found an output size mismatch between "
                        f"fake shape {s_fake} and real shape {s_real}, "
                        f"at output{keystr(path)}.size({j}), for func: {func}"
                    ) from exc
        elif fake is None and real is not None:
            if torch._functorch.config.generate_fake_kernels_from_real_mismatches:
                dtrace_structured(
                    "mismatched_fake_kernel",
                    metadata_fn=lambda: {
                        "op": str(func),
                        "reason": f"mismatch between fake value {fake} and real value {real}",
                    },
                )
                return _infer_fake_from_real_tensor(self, func, real), True  # type: ignore[arg-type]
            raise MetadataMismatchError(
                f"Real tensor propagation found a metadata mismatch between "
                f"fake tensor {fake} and real tensor {real}, "
                f" at output{keystr(path)}, for func: {func}"
            )
        else:
            try:
                _check_fake_real_vals(fake, real)
            except MetadataMismatchError as exc:
                raise MetadataMismatchError(
                    f"Real tensor propagation found an output value mismatch between "
                    f"fake output value {fake} and real output value {real}, "
                    f"at output{keystr(path)}, for func: {func}"
                ) from exc
        return fake, False