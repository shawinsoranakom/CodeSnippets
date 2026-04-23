def test_partitioner(self, fn, expected_partition, bookend_non_compute_pass):
        traced = symbolic_trace(fn)

        non_compute_ops = []
        if bookend_non_compute_pass:
            non_compute_ops = ["torch.ops.aten.view", "torch.ops.aten.permute"]

        supported_ops = MockOperatorSupport()
        partitioner = CapabilityBasedPartitioner(traced,
                                                 supported_ops,
                                                 allows_single_node_partition=True,
                                                 non_compute_ops=non_compute_ops)
        partitions = partitioner.propose_partitions()
        if bookend_non_compute_pass:
            partitioner.remove_bookend_non_compute_ops(partitions)

        partitions_name = [[node.name for node in partition.nodes] for partition in partitions]
        if len(partitions_name) != len(expected_partition):
            raise AssertionError(f"partition count mismatch: {len(partitions_name)} != {len(expected_partition)}")
        for i in range(len(partitions_name)):
            if set(partitions_name[i]) != set(expected_partition[i]):
                raise AssertionError(f"partition {i} mismatch: {set(partitions_name[i])} != {set(expected_partition[i])}")

        fused_graph = partitioner.fuse_partitions(partitions)

        a, b, c = torch.rand(4), torch.rand(4), torch.rand(4)

        expected = fn(a, b, c)
        result = fused_graph(a, b, c)
        torch.testing.assert_close(expected, result)