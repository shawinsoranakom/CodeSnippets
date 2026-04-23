def verify_pytree(f, inp):
            val = pytree.tree_map(
                lambda x: torch.randn(3) if isinstance(x, PHBase) else x, inp
            )
            num_flat_args = len(pytree.tree_leaves(inp))
            orig_out = f(val)
            nf = symbolic_trace(f, concrete_args={"x": inp})
            self.assertEqual(nf(val), orig_out)

            bare_fx = GraphModule({}, copy.deepcopy(nf.graph))
            bare_fx.graph.set_codegen(CodeGen())
            bare_fx.recompile()
            self.assertEqual(
                nf.graph.process_outputs(bare_fx(*nf.graph.process_inputs(val))),
                orig_out,
            )

            if not (num_flat_args == 0 or "tree_flatten_spec" in nf.code):
                raise AssertionError(
                    "Expected tree_flatten_spec in nf.code when num_flat_args > 0"
                )
            placeholder_count = sum(i.op == "placeholder" for i in nf.graph.nodes)
            if placeholder_count != num_flat_args:
                raise AssertionError(
                    f"Expected {num_flat_args} placeholders, got {placeholder_count}"
                )

            nf = symbolic_trace(nf)
            self.assertEqual(nf(val), orig_out)
            if "tree_flatten_spec" in nf.code:
                raise AssertionError("Expected tree_flatten_spec not in nf.code")
            placeholder_count = sum(i.op == "placeholder" for i in nf.graph.nodes)
            if placeholder_count != 1:
                raise AssertionError(
                    f"Expected 1 placeholder, got {placeholder_count}"
                )

            nf = symbolic_trace(nf, concrete_args={"x": inp})
            self.assertEqual(nf(val), orig_out)
            if not (num_flat_args == 0 or "tree_flatten_spec" in nf.code):
                raise AssertionError(
                    "Expected tree_flatten_spec in nf.code when num_flat_args > 0"
                )
            placeholder_count = sum(i.op == "placeholder" for i in nf.graph.nodes)
            if placeholder_count != num_flat_args:
                raise AssertionError(
                    f"Expected {num_flat_args} placeholders, got {placeholder_count}"
                )

            pickled = pickle.dumps(nf)
            nf = pickle.loads(pickled)
            self.assertEqual(nf(val), orig_out)