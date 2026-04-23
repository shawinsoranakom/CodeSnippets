def check_skip_condition(inp_out_node, is_output):
        if not isinstance(inp_out_node, torch.fx.Node):
            return False

        if "val" not in inp_out_node.meta:
            return False

        for meta in pytree.tree_leaves(inp_out_node.meta["val"]):
            if not isinstance(meta, torch._subclasses.FakeTensor):
                continue

            if is_output:
                if unsupported_output_tensor(meta, node):
                    return True
            else:
                if unsupported_input_tensor(meta, node):
                    return True

        return False