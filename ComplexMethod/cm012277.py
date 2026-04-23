def _eliminate_duplicate_packed_nodes(gm):
        """
        Combine packed weight nodes with the same inputs to reduce memory usage.
        for example:
        class Model(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.linear = nn.Linear(32, 32, bias=True)

            def forward(self, x):
                return self.linear(self.linear(x))

        the above's packed weight nodes are duplicate if two linear calls have same input size.
        """
        if not (torch.backends.mkldnn.enabled and torch.backends.mkldnn.is_available()):
            return gm

        packed_weight_ops = [
            torch._C._nn.mkldnn_reorder_conv2d_weight,
            torch._C._nn.mkldnn_reorder_conv3d_weight,
            mkldnn._reorder_convolution_transpose_weight,
            mkldnn._reorder_linear_weight,
            mkldnn._reorder_mkldnn_rnn_layer_weight,
        ]
        if torch._C.has_mkl:
            packed_weight_ops.append(torch.ops.mkl._mkl_reorder_linear_weight)

        for node in gm.graph.nodes:
            if node.target in packed_weight_ops and len(node.args[0].users) > 1:
                for user_node in list(node.args[0].users.keys()):
                    if (
                        user_node.target == node.target
                        and user_node != node
                        and user_node.args == node.args
                    ):
                        user_node.replace_all_uses_with(node)
                        gm.graph.erase_node(user_node)