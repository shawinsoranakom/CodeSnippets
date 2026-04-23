def _to_fake_tensor(t: MetaTensorDesc[Any]) -> _TensorT:
                        # TODO: why aren't the recursive calls going to
                        # meta_tensor
                        r: _TensorT
                        if t.is_batchedtensor:
                            if t.unwrapped is None:
                                raise AssertionError(
                                    "t.unwrapped must not be None for batchedtensor"
                                )
                            if t.level is None:
                                raise AssertionError(
                                    "t.level must not be None for batchedtensor"
                                )
                            if t.bdim is None:
                                raise AssertionError(
                                    "t.bdim must not be None for batchedtensor"
                                )
                            ft = _to_fake_tensor(t.unwrapped)
                            lvl = t.level
                            bdim = t.bdim
                            # You cannot create functorch tensors without
                            # having the ambient funtorch interpreter stack
                            # available, as the level refers to things in the
                            # stack
                            with torch._functorch.pyfunctorch.temporarily_restore_interpreter_stack(
                                t.functorch_stack
                            ):
                                r = self._checked_cast_tensor_t(
                                    _add_batch_dim(ft, bdim, lvl)
                                )
                        elif t.is_gradtrackingtensor:
                            if t.unwrapped is None:
                                raise AssertionError(
                                    "t.unwrapped must not be None for gradtrackingtensor"
                                )
                            if t.level is None:
                                raise AssertionError(
                                    "t.level must not be None for gradtrackingtensor"
                                )
                            disable_functorch = torch._C._DisableFuncTorch
                            with disable_functorch():
                                ft = _to_fake_tensor(t.unwrapped)
                            lvl = t.level
                            if lvl == GRAD_TENSOR_SENTINEL_VALUE:
                                r = ft
                            else:
                                with torch._functorch.pyfunctorch.temporarily_restore_interpreter_stack(
                                    t.functorch_stack
                                ):
                                    r = self._checked_cast_tensor_t(
                                        torch._C._functorch._wrap_for_grad(ft, lvl),
                                    )

                            is_leaf = t.is_leaf
                            if t.requires_grad and safe_is_leaf(r):
                                r.requires_grad = True
                            elif t.requires_grad and not is_leaf:
                                r = self._backward_error(r)
                        elif t.is_functional:
                            if t.unwrapped is None:
                                raise AssertionError(
                                    "t.unwrapped must not be None for functional tensor"
                                )
                            if t.current_level is None:
                                raise AssertionError(
                                    "t.current_level must not be None for functional tensor"
                                )
                            ft = self.meta_tensor(
                                t.unwrapped,
                                shape_env,
                                callback,
                                # NB: reuse these exactly, we treat the
                                # functional tensor as "invisible".
                                # TODO: Actually this all probably doesn't
                                # work, take a closer look.
                                source,
                                symbolic_context,
                            )
                            r = self._checked_cast_tensor_t(
                                _wrap_functional_tensor(ft, t.current_level),
                            )
                            # TODO: is_leaf/requires_grad?
                        else:
                            if t.stride is None:
                                raise AssertionError("t.stride must not be None")

                            sizes = t.size
                            strides = t.stride
                            r = callback(
                                lambda: torch.empty_strided(
                                    sizes,
                                    strides,
                                    dtype=t.dtype,
                                    device="meta",
                                ),
                                # device="meta",
                            )
                            if self.copy_data:
                                with torch.no_grad(), no_dispatch():
                                    r.real_tensor = torch.empty_strided(  # type: ignore[attr-defined]
                                        t.size,
                                        t.stride,
                                        dtype=t.dtype,
                                        device=t.device,
                                    )
                                    if t.data is None:
                                        raise AssertionError(
                                            "t.data must not be None when copy_data is True"
                                        )
                                    _safe_copy(r.real_tensor, t.data)  # type: ignore[attr-defined]
                        # pyrefly: ignore [bad-return]
                        return r