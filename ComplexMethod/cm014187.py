def handle_saved_tensors_wiring(
        self,
        fwd_out: VariableTracker,
        fwd_graph: torch.fx.Graph,
        fwd_freevars: dict[Proxy, Proxy],
        fwd_graph_body_outputs: Sequence[VariableTracker],
        bwd_graph: torch.fx.Graph,
        bwd_freevars: dict[Proxy, Proxy],
    ) -> tuple[torch.fx.Graph, torch.fx.Graph]:
        # ---------------------------------------------------------------------
        # Rewiring Forward Outputs to Backward Inputs (and Handling Saved Tensors)
        #
        # In `rewire_bwd_graph_outputs`, we aligned the *forward inputs* with the
        # *backward outputs*. This method performs the complementary task:
        # aligning the *forward outputs* with the *backward inputs*, while also
        # incorporating all tensors saved via ctx.save_for_backward.
        #
        # There are two main issues we must resolve:
        #
        # (1) Forward outputs may contain non-tensor values.
        #     This means the number of tensors visible in fwd_out may not match
        #     the number of tensors produced by the traced forward graph. As a
        #     result, the backward graph’s placeholders may not line up with the
        #     actual tensor outputs.
        #
        # (2) The backward graph may require intermediate tensors saved during
        #     the forward pass (via save_for_backward), but those intermediates
        #     might not currently be included among the forward graph’s outputs.
        #
        # Together, these issues mean that the bwd_graph input signature may be
        # inconsistent with what fwd_graph outputs, and we need to rewrite both.
        #
        # Lets look at an example to understand the transformation
        #
        # class Add(torch.autograd.Function):
        #     @staticmethod
        #     def forward(ctx, x, y):
        #         a = torch.sin(x)
        #         b = torch.cos(y)
        #         ctx.save_for_backward(a)
        #         return Foo(a, b), x * y

        #     @staticmethod
        #     def backward(ctx, grad_a, grad_b):
        #         (a,) = ctx.saved_tensors
        #         return grad_b * 2, a * grad_b * 3

        # Before
        # fwd_graph():
        #     %l_x_ : torch._subclasses.fake_tensor.FakeTensor [num_users=2] = placeholder[target=l_x_]
        #     %l_y_ : torch._subclasses.fake_tensor.FakeTensor [num_users=2] = placeholder[target=l_y_]
        #     ....
        #     return (a, b, out)
        #
        # bwd_graph():
        #     %grad_b : torch.Tensor [num_users=2] = placeholder[target=grad_b]
        #     %a : torch._subclasses.fake_tensor.FakeTensor [num_users=1] = placeholder[target=a]
        #     ....
        #     return (mul, mul_2)
        #
        # The problems here:
        #   (1) fwd_graph has 3 tensor outputs (a, b, out), but bwd_graph has
        #       only 1 gradient input - grad_b. We need 3.
        #
        #   (2) bwd_graph uses `a` (a saved tensor) as an input, but fwd_graph
        #       does not currently return `a`. To make `a` available to the
        #       backward graph, the forward graph must expose it as part of its
        #       output signature.
        #
        # After this transformation
        # fwd_graph():
        #     %l_x_ : torch._subclasses.fake_tensor.FakeTensor [num_users=2] = placeholder[target=l_x_]
        #     %l_y_ : torch._subclasses.fake_tensor.FakeTensor [num_users=2] = placeholder[target=l_y_]
        #     .....
        #     return ((a, b, out), (a,))
        # bwd_graph():
        #     %unused_0 : [num_users=0] = placeholder[target=unused_0]
        #     %unused_1 : [num_users=0] = placeholder[target=unused_1]
        #     %grad_b : [num_users=2] = placeholder[target=grad_b]
        #     %a : [num_users=1] = placeholder[target=a]
        #     .....
        #     return (mul, mul_2)
        #
        # Key changes:
        #
        #   1) The forward graph now returns:
        #           (existing_outputs), (saved_tensors)
        #      This exposes saved intermediates (`a`) as part of the fwd output
        #      structure, making them available to backward.
        #
        #   2) The backward graph input signature is rewritten to:
        #           (*grads_for_existing_outputs, *saved_tensors)
        #      This ensures the counts and ordering match the new fwd_graph
        #      output structure. Placeholders corresponding to tensors whose
        #      gradients are unused (e.g., `a`, `b`) appear as `%unused_*`.
        #
        # This alignment ensures that the synthesized autograd.Function follows
        # PyTorch’s forward/backward calling convention and that all required
        # saved tensors are available to the backward graph.
        # ---------------------------------------------------------------------

        # To address Problem (1), we must determine which backward-graph inputs
        # correspond to the forward-graph outputs.
        #
        # We use two facts:
        #   • `fwd_out` preserves the original forward output order.
        #   • Backward-graph inputs are also ordered according to the backward()
        #     method signature, thanks to automatic_with_forced_inputs.
        #
        # For any forward output that is *not* a tensor, there is no
        # corresponding tensor placeholder in the backward graph. During tracing,
        # we intentionally inserted a `None` VariableTracker for these positions,
        # so the backward graph contains no placeholder for them.
        bwd_input_nodes = list(bwd_graph.find_nodes(op="placeholder"))
        # pyrefly: ignore [implicit-any]
        fwd_vt_to_bwd_node = {}
        bwd_idx = 0
        if isinstance(fwd_out, variables.BaseListVariable):
            for fwd_vt in fwd_out.items:
                if fwd_vt.is_tensor():
                    fwd_vt_to_bwd_node[fwd_vt] = bwd_input_nodes[bwd_idx]
                    bwd_idx += 1
        else:
            if fwd_out.is_tensor():
                fwd_vt_to_bwd_node[fwd_out] = bwd_input_nodes[bwd_idx]
                bwd_idx += 1

        rewired_bwd_graph_inputs = []
        for fwd_graph_vt in fwd_graph_body_outputs:
            # for tensor vts that were part of a user-defined object (like in
            # the above example), we just set None for now. Later, we will use
            # these None to insert a unused placeholder.
            # type: ignore[arg-type]
            rewired_bwd_graph_inputs.append(fwd_vt_to_bwd_node.get(fwd_graph_vt))

        # To address Problem (2), we must incorporate any tensors that were saved
        # (or otherwise smuggled) from the forward pass into the backward graph.
        #
        # Fortunately, these are easy to identify: they appear in `bwd_freevars`.
        # `bwd_freevars` maps outer-graph lifted proxies to inner-graph placeholder
        # proxies. Because the backward graph is traced using proxies originating
        # from `fwd_out`, any value lifted into the backward graph represents a
        # saved/smuggled tensor.
        #
        # Once we identify these saved tensors, we must also locate their
        # corresponding forward-graph proxies so that the forward graph can return
        # these tensors as part of its output signature.
        extra_fwd_output_nodes = []
        for fwd_proxy, bwd_inner_proxy in bwd_freevars.items():
            # For backward, its easy, just get the node from bwd_inner_proxy
            rewired_bwd_graph_inputs.append(bwd_inner_proxy.node)

            # For the fwd_proxy, it could be a proxy from the outer graph, or it
            # could be an intermediate.
            # First ensure that's its inner fwd proxy
            inner_fwd_proxy = fwd_freevars.get(fwd_proxy, fwd_proxy)
            extra_fwd_output_nodes.append(inner_fwd_proxy.node)

        # Mechanical steps from here on. We have the extra_fwd_outputs and rewired_bwd_inputs. Lets make the changes.
        # Lets change the fwd graph outputs.
        # pyrefly: ignore [implicit-any]
        fwd_output_nodes = []
        for node in fwd_graph.find_nodes(op="output"):
            fwd_output_nodes = node.args[0]
            fwd_graph.erase_node(node)
            break

        # The signature is now ((*existing_outputs), (*extra_outputs)). Please
        # take a look at AutogradFunctionApply where we take the saved_tensors
        # out in the forward method to save for backward.
        new_fwd_graph_outputs = (fwd_output_nodes, tuple(extra_fwd_output_nodes))
        fwd_graph.output(new_fwd_graph_outputs)
        fwd_graph.lint()

        # Now lets change the bwd graph.
        new_graph = torch.fx.Graph()
        env = {}

        count = itertools.count()

        for node in rewired_bwd_graph_inputs:
            if node is None:
                new_node = new_graph.placeholder(f"unused_{next(count)}")
            else:
                new_node = new_graph.placeholder(node.name)
                new_node.meta = copy.copy(node.meta)
            env[node] = new_node

        for node in bwd_graph.nodes:
            if node.op == "placeholder":
                assert node in env
            else:
                env[node] = new_graph.node_copy(node, lambda x: env[x])
                env[node].meta = copy.copy(node.meta)

        new_graph.lint()
        return fwd_graph, new_graph