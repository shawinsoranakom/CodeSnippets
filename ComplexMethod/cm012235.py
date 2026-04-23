def match(self, node: torch.fx.Node) -> tuple[str, int, int, int, bool, str] | None:
        if CallFunctionVarArgs(aten.mm).match(node):
            input_m, weight_m = node.args
            bias_m = None

        elif CallFunctionVarArgs(aten.addmm.default).match(
            node
        ) and self._addmm_node_can_be_fused(node):
            bias_m, input_m, weight_m = node.args
        else:
            return None
        # get the user of the node
        if self.graph_search_options.get("fuse_nodes_with_same_users", False):
            users = [user.target for user in node.users]
        else:
            users = ""  # type: ignore[assignment]
        # only handle the cases where inputs are 2D tensors
        if not self._is_input_2d(input_m) or not self._is_input_2d(weight_m):  # type: ignore[arg-type]
            return None
        m, k = input_m.meta["val"].shape  # type: ignore[union-attr]
        n = weight_m.meta["val"].shape[1]  # type: ignore[union-attr]
        batch_key = ("batch_linear_post_grad", m, k, n, bias_m is not None, str(users))
        return batch_key