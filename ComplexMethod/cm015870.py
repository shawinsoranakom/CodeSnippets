def fx_pass_backend(gm, example_inputs):
            # Walk the graph and set hints on unbacked SymInts
            for node in gm.graph.nodes:
                if (
                    node.op == "call_function"
                    and node.target is torch.ops.aten.item.default
                ):
                    # The node's example value is a SymInt from .item()
                    sym_val = node.meta.get("example_value", None)
                    if sym_val is not None and isinstance(sym_val, torch.SymInt):
                        torch._dynamo.override_optimization_hint(sym_val, 512)

            # Verify the hint was set on shape_env
            shape_env = None
            for node in gm.graph.nodes:
                if (
                    node.op == "call_function"
                    and node.target is torch.ops.aten.item.default
                ):
                    sym_val = node.meta.get("example_value", None)
                    if sym_val is not None and isinstance(sym_val, torch.SymInt):
                        shape_env = sym_val.node.shape_env
                        expr = sym_val.node.expr
                        if expr not in shape_env.var_to_hint_override:
                            raise AssertionError("hint not set on shape_env")
                        if shape_env.var_to_hint_override[expr] != 512:
                            raise AssertionError("hint value mismatch")

            return gm