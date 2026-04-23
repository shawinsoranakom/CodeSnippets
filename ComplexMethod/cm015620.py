def test_partitioner_offload_ao_ops_prefetch(self):
        """Test that prefetch moves ao.reload earlier in backward graph."""
        reset_user_object_tracking()
        torch._dynamo.reset()
        with torch._functorch.config.patch(
            enable_activation_offloading=True,
            activation_offload_separate_stream=True,
            activation_reload_prefetch=True,
            joint_custom_pass=self.joint_custom_pass,
        ):
            _, bw_graph = get_fw_bw_graph(self.fn, [self.x])

        nodes = list(bw_graph.graph.nodes)
        reload_nodes = [
            n
            for n in nodes
            if n.op == "call_function" and n.target == torch.ops.ao.reload.default
        ]
        wait_nodes = [
            n
            for n in nodes
            if n.op == "call_function"
            and n.target == torch.ops.ao.wait_tensor.default
            and isinstance(n.args[0], torch.fx.Node)
            and n.args[0].target == torch.ops.ao.reload.default
        ]
        # Reload should appear before its corresponding wait (prefetched earlier)
        for reload_node in reload_nodes:
            wait_node = next(w for w in wait_nodes if w.args[0] is reload_node)
            self.assertLess(nodes.index(reload_node), nodes.index(wait_node))