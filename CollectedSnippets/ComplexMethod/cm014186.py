def rewire_bwd_graph_outputs(
        self,
        fwd_freevars: dict[Proxy, Proxy],
        bwd_out: VariableTracker,
        bwd_graph: torch.fx.Graph,
        bwd_freevars: dict[Proxy, Proxy],
        orig_fwd_args: Sequence[VariableTracker],
    ) -> None:
        # ---------------------------------------------------------------------
        # Forward–Backward Input/Output Alignment
        #
        # autograd.Function requires that the outputs of backward() correspond
        # exactly to the inputs of forward(). Normally this alignment is the
        # user’s responsibility. However, when Dynamo synthesizes a new
        # autograd.Function for a traced region, Dynamo must perform this
        # alignment automatically.
        #
        # To do this, Dynamo uses the *original* forward call site as the anchor
        # that defines how forward inputs map to backward outputs.
        #
        # ---------------------------------------------------------------------
        # Terminology
        #
        # fwd_freevars / bwd_freevars:
        #     Maps from *outer-graph proxies* to *inner-graph placeholder
        #     proxies*. Keys are always outer-graph proxies (these may be actual
        #     user inputs or intermediate values lifted into the subgraph).
        #
        # orig_fwd_args:
        #     VariableTrackers for the forward() inputs. Since these correspond
        #     to user-exposed arguments, each tracker points to an *outer-graph*
        #     proxy.
        #
        # bwd_outs:
        #     VariableTrackers for the backward() outputs. These usually point to
        #     *inner-graph* proxies, except for cases where a forward input is
        #     passed directly through to a backward output—in which case the
        #     tracker may still refer to an outer-graph proxy.
        #
        # ---------------------------------------------------------------------
        # Goal
        #
        # To ensure forward–backward consistency, we must rewire the backward
        # graph outputs so that they line up with the forward graph inputs.
        #
        # We build a mapping from outer-graph proxy → inner-graph proxy using
        # orig_fwd_args and bwd_outs, then iterate over the fwd_graph inputs to
        # determine which backward outputs must be generated (or padded with
        # None) to satisfy autograd’s calling convention.
        #
        # ---------------------------------------------------------------------
        # Example
        #
        # Suppose the forward receives a user-defined object:
        #
        # @dataclass
        # class Weird:
        #     x: int
        #     b: torch.Tensor
        #     c: torch.Tensor
        #
        # class Foo(torch.autograd.Function):
        #     @staticmethod
        #     def forward(ctx, x: torch.Tensor, weird: Weird, z: torch.Tensor):
        #         ctx.save_for_backward(weird.b, weird.c)
        #         return weird.b * weird.c * x.clone()
        #
        #     @staticmethod
        #     def backward(ctx, grad):
        #         b, c = ctx.saved_tensors
        #         return grad * b * c, None, grad * 2
        #
        # Dynamo lifts the tensor fields of the user-defined object for the trace:
        #
        # fwd_graph():
        #     %l_weird_b : FakeTensor = placeholder[target=l_weird_b]
        #     %l_weird_c : FakeTensor = placeholder[target=l_weird_c]
        #     %l_x_      : FakeTensor = placeholder[target=l_x_]
        #     %l_z_      : FakeTensor = placeholder[target=l_z_]
        #     ...
        #     return (outs,)
        #
        # The initial backward graph:
        #
        # bwd_graph():
        #     %grad       : Tensor    = placeholder[target=grad]
        #     %l_weird_b  : FakeTensor = placeholder[target=l_weird_b]
        #     %l_weird_c  : FakeTensor = placeholder[target=l_weird_c]
        #     ...
        #     return (mul_1, mul_2)
        #
        # The forward graph has 4 inputs, but the backward graph produces only 2
        # outputs, and their ordering does not match the forward argument order.
        #
        # So Dynamo rewires the backward graph outputs to align with the forward
        # inputs:
        #
        # bwd_graph():
        #     ...
        #     return (None, None, mul_1, mul_2)
        #
        # This ensures the synthesized autograd.Function conforms to PyTorch’s
        # forward/backward contract.
        # ---------------------------------------------------------------------

        def get_bwd_node(vt: VariableTracker) -> torch.fx.Node:
            # Backward tensor vt here can be - (1) an intermediate, or (2) input
            # to the backward graph. If it is an input to the backward graph, we have to lookup bwd_freevars to get the inner proxy.
            return bwd_freevars.get(vt.proxy, vt.proxy).node  # type: ignore[attr-defined]

        # Find the mapping between orig_fwd_args and bwd_out
        # pyrefly: ignore [implicit-any]
        outer_fwd_proxy_to_bwd_node = {}
        if isinstance(bwd_out, variables.BaseListVariable):
            bwd_outs = bwd_out.items
            for idx, fwd_arg in enumerate(orig_fwd_args):
                # We care about tensor args. For non-tensor args, the bwd output returns None.
                if fwd_arg.is_tensor():
                    bwd_out_at_idx = bwd_outs[idx]
                    if bwd_out_at_idx.is_tensor():
                        # type: ignore[attr-defined]
                        outer_fwd_proxy_to_bwd_node[fwd_arg.proxy] = get_bwd_node(
                            bwd_out_at_idx
                        )
                    else:
                        # backward can return None at the output
                        assert (
                            isinstance(bwd_out_at_idx, variables.ConstantVariable)
                            and bwd_out_at_idx.value is None
                        )
                        # type: ignore[attr-defined]
                        outer_fwd_proxy_to_bwd_node[fwd_arg.proxy] = None

        elif bwd_out.is_tensor():
            # type: ignore[attr-defined]
            outer_fwd_proxy_to_bwd_node[orig_fwd_args[0].proxy] = get_bwd_node(bwd_out)

        # Ideally, we should have walked through the fwd placeholders. But we
        # can instead walk through the fwd_freevars, which is a insertion sorted
        # dictionary and therefore represents the outer_proxies for the
        # placeholder in the same order as that as placeholders.
        rewired_bwd_outputs = [
            outer_fwd_proxy_to_bwd_node.get(fwd_proxy) for fwd_proxy in fwd_freevars
        ]

        for node in bwd_graph.find_nodes(op="output"):
            bwd_graph.erase_node(node)
            break
        bwd_graph.output(tuple(rewired_bwd_outputs))
        bwd_graph.lint()