def create_deferred_runtime_asserts(
        self, n: torch.fx.Node, new_unbacked_defs: OrderedSet[sympy.Symbol]
    ) -> None:
        if config.do_not_emit_runtime_assertions:
            return
        # [NOTE] Codegen runtime asserts in Inductor
        #
        # We need to generate runtime asserts directly in Inductor instead
        # of just reusing the asserts from input graphs because we reuse the
        # same ShapeEnv as before. In particular, on subsequent graph passes,
        # we would immediately turn all of these assertions into noops,
        # because when we evaluated their expressions, we would see that
        # because we had a deferred runtime assert in the ShapeEnv, we
        # know "oh, of course this expression is True" already.
        # One example is below:
        #
        # class Model(torch.nn.Module):
        #     def forward(self, a, b, c):
        #         nz = torch.nonzero(a)
        #         ones = a.new_ones([nz.size(0), b.size(0)])
        #         torch._check(ones.size(0) >= 1)
        #         equals = torch.add(ones, c)
        #         return equals
        # torch._dynamo.mark_dynamic(c, 0)
        # When we reuse the ShapeEnv in Inductor lowering, the check that checks
        # a and nonzero have the same shape would be evaluated to True after we resolve
        # unbacked bindings using the ShapeEnv.
        # See test_unbacked_equals_input_size_runtime_assertion in test_aot_inductor.
        #
        #
        # In addition to the Inductor generated runtime asserts, we also
        # need the runtime asserts from the input graph, because some derived
        # runtime asserts on backed symints are not generated in Inductor. One example is
        # this: `y = x.reshape(100, -1).clone()`. x.shape[0] needs to be a multiple of 100.
        # See test_aoti_runtime_asserts_backed_symint in test_aot_inductor.

        def make_assert(expr: SympyBoolean, msg: str) -> None:
            assert_op = ir.AssertScalar(expr, msg)
            self.register_buffer(assert_op, set_name=True)
            self.register_operation(assert_op)

        if (
            full_aoti_runtime_assert()
            and n.target is torch.ops.aten._assert_scalar.default
            and self.aot_mode
        ):
            node_args, _ = self.fetch_args_kwargs_from_env(n)
            if node_args[0] != True:  # noqa: E712
                make_assert(node_args[0], f"{node_args[0]} to be True")
        else:
            # bound_unbacked_symbols tracks the symbols that are created so far,
            # we use it to make sure that runtime assertions are added after all
            # symbols used in them are defined.
            self.bound_unbacked_symbols |= new_unbacked_defs

            shape_env = V.graph.sizevars.shape_env

            # Emit code for runtime asserts that can be inserted at this point.
            for i0 in new_unbacked_defs:
                ras = self.ras_by_symbol.pop(i0, [])
                # NB: size-like not needed, we won't retrace
                vr = shape_env.var_to_range[i0]
                if not shape_env._default_unspecified_value_range().issubset(vr):

                    def is_convertible(s: Expr) -> bool:
                        if s in (int_oo, -int_oo):
                            return False
                        try:
                            int(s)
                            return True
                        except TypeError:
                            return False

                    if is_convertible(vr.lower):
                        make_assert(i0 >= vr.lower, f"{i0} >= {vr.lower}")
                    if is_convertible(vr.upper):
                        make_assert(i0 <= vr.upper, f"{i0} <= {vr.upper}")

                for ra in ras:
                    fvs = free_unbacked_symbols(ra.expr)
                    missing = fvs - self.bound_unbacked_symbols
                    if missing:
                        i1 = min(missing, key=str)
                        self.ras_by_symbol.setdefault(i1, []).append(ra)
                    else:
                        make_assert(ra.expr, f"{ra.expr}")