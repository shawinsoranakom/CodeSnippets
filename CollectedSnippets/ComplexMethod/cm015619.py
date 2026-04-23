def test_partitioner_offload_ao_ops_sink_wait(self):
        """Test that sink_wait moves ao.wait_tensor for offload to end of forward graph."""
        reset_user_object_tracking()
        torch._dynamo.reset()
        with torch._functorch.config.patch(
            enable_activation_offloading=True,
            activation_offload_separate_stream=True,
            activation_offload_sink_wait=True,
            joint_custom_pass=self.joint_custom_pass,
        ):
            fw_graph, _ = get_fw_bw_graph(self.fn, [self.x])

        # The ao.wait_tensor for offload should be sunk to just before the output node
        nodes = list(fw_graph.graph.nodes)
        output_node = next(n for n in nodes if n.op == "output")
        output_idx = nodes.index(output_node)

        for node in nodes:
            if (
                node.op == "call_function"
                and node.target == torch.ops.ao.wait_tensor.default
                and isinstance(node.args[0], torch.fx.Node)
                and node.args[0].target == torch.ops.ao.offload.default
            ):
                wait_idx = nodes.index(node)
                # ao.wait_tensor should be immediately before output
                self.assertEqual(wait_idx, output_idx - 1)