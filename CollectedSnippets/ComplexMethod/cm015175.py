def __torch_dispatch__(self, func, types, args=(), kwargs=None):
            self.test_case.precision = self.saved_precision
            self.test_case.rel_tol = self.saved_rel_tol

            self.called.add(func)
            all_called[func] += 1

            # Stuff we shouldn't bother testing
            # (TODO: remove detach from the decomp table?)
            # N.b. Testing in-place ops would need dedicated logic
            in_place = func.name()[-1] == "_"
            ignored_ops = [
                torch.ops.aten.detach.default,
                # non-deterministic ops
                torch.ops.aten.empty.memory_format,
                torch.ops.aten.empty_like.default,
                torch.ops.aten.new_empty.default,
                torch.ops.aten.empty_strided.default,
                torch.ops.aten.new_empty_strided.default,
                torch.ops.aten.randn.default,
                torch.ops.aten.native_dropout.default,
            ]
            if (
                func not in decomposition_table
                or func in ignored_ops
                or torch.Tag.nondeterministic_seeded in func.tags
                or any_unsupported(args, kwargs)
                or in_place
            ):
                return func(*args, **kwargs)

            self.decomposed.add(func)
            all_decomposed.add(func)

            # We take 2 main strategies for verifying correctness/numerical stability of decompositions
            # The first one is simply tolerance checking between decomp_out and pytorch_out
            # However, for fp16/bf16 and reductions, this becomes very
            # finicky, as there are not many guarantees we can make.
            # So, for fp16/bf16, we instead compare the difference of
            # {decomp_out, pytorch_out_64} and {pytorch_out,
            # pytorch_out_64}. In other words, we compare how far the
            # decomposition and pytorch are from the "ground truth" (i.e.
            # fp64). If the decomposition results in more error, we error

            # We also decompose the decomposition recursively for
            # further coverage, as some paths not be exercised directly by
            # OpInfos (sadly) but just by other ops

            decomposition = decomposition_table[func]

            do_relative_check = self.test_dtype in [torch.float16, torch.bfloat16]
            if self.run_all:
                # Execute recursively via DFS, to find the root of a possible error first
                with self:
                    decomp_out = pytree.tree_leaves(decomposition(*args, **kwargs))
            else:
                decomp_out = pytree.tree_leaves(decomposition(*args, **kwargs))

            # At this stage we should not be decomposing an in-place op
            # We'd like to have decompositions that decompose out-of-place ops into out-of-place ops
            #  because decompositions are run after functionalisation and we would not like them to
            #  de-functionalise the graph, as that would break AoTAutograd
            # We run the real function *after* the decomposition to make sure that the
            # decomposition does not modify any of the inputs in-place. If it does
            # real_out should be different than decom_out so we should catch this
            real_out_unflat = func(*args, **kwargs)
            real_out = pytree.tree_leaves(real_out_unflat)

            if len(real_out) != len(decomp_out):
                raise AssertionError(
                    f"output length mismatch: {len(real_out)} != {len(decomp_out)}"
                )

            if do_relative_check:
                device_arg = kwargs.get("device", None)

                def upcast(x):
                    if (isinstance(x, Tensor) and x.device.type == "mps") or (
                        device_arg and torch.device(device_arg).type == "mps"
                    ):
                        return upcast_tensor(x, dtype=torch.float32)
                    else:
                        return upcast_tensor(x, dtype=torch.float64)

                real_out_double, _ = tree_flatten(
                    func(*tree_map(upcast, args), **tree_map(upcast, kwargs))
                )
                for i, (orig, decomp, ref) in enumerate(
                    zip(real_out, decomp_out, real_out_double)
                ):
                    if not isinstance(orig, torch.Tensor):
                        if type(orig) is not type(decomp):
                            raise AssertionError(
                                f"type mismatch: {type(orig)} != {type(decomp)}"
                            )
                        if orig != decomp:
                            raise AssertionError(f"value mismatch: {orig} != {decomp}")
                        continue
                    op_assert_ref(
                        self.test_case,
                        func,
                        self.test_dtype,
                        i,
                        orig,
                        decomp,
                        ref,
                        args,
                        kwargs,
                    )
            else:
                for orig, decomp in zip(real_out, decomp_out):
                    if not isinstance(orig, torch.Tensor):
                        if type(orig) is not type(decomp):
                            raise AssertionError(
                                f"type mismatch: {type(orig)} != {type(decomp)}"
                            )
                        if orig != decomp:
                            raise AssertionError(f"value mismatch: {orig} != {decomp}")
                        continue
                    op_assert_equal(
                        self.test_case,
                        func,
                        self.test_dtype,
                        orig,
                        decomp,
                        args,
                        kwargs,
                    )

            return real_out_unflat