def test_partitioner_nested_getitem_chains(self):
        """Test that nested getitem chains are properly reassigned to producer's partition.

        this tests the fix for handling patterns like:
            producer_node = call(...)  # returns ((a, b), c)
            getitem_1 = producer_node[0]  # gets (a, b)
            getitem_2 = getitem_1[0]  # gets a

        without the iterative fix, getitem_2 would be assigned to getitem_1's original
        partition instead of the producer's partition.
        """
        traced = symbolic_trace(TestNestedGetitemFunctions.forward_nested_getitem_cross_partition)

        supported_ops = MockOperatorSupport()
        partitioner = CapabilityBasedPartitioner(
            traced,
            supported_ops,
            allows_single_node_partition=True
        )
        partitions = partitioner.propose_partitions()

        node_to_partition: dict[torch.fx.Node, int] = {}
        for idx, partition in enumerate(partitions):
            for node in partition.nodes:
                node_to_partition[node] = idx

        producer_node = None
        getitem_nodes = []
        for node in traced.graph.nodes:
            if node.op == "call_function":
                if node.target == _nested_tuple_producer:
                    producer_node = node
                elif node.target == operator.getitem:
                    getitem_nodes.append(node)

        self.assertIsNotNone(producer_node, "Should find the nested tuple producer node")
        self.assertGreaterEqual(len(getitem_nodes), 3, "Should find at least 3 getitem nodes")

        # all getitems that derive from the producer (including nested ones)
        # should be in the same partition as the producer
        if producer_node in node_to_partition:
            producer_partition = node_to_partition[producer_node]

            for getitem_node in getitem_nodes:
                current = getitem_node.args[0]
                derives_from_producer = False
                while hasattr(current, 'op'):
                    if current == producer_node:
                        derives_from_producer = True
                        break
                    if current.op == "call_function" and current.target == operator.getitem:
                        current = current.args[0]
                    else:
                        break

                if derives_from_producer:
                    getitem_partition = node_to_partition.get(getitem_node)
                    self.assertEqual(
                        getitem_partition,
                        producer_partition,
                        f"Getitem node '{getitem_node.name}' (nested in chain from producer) "
                        f"should be in same partition as producer. "
                        f"Got partition {getitem_partition}, expected {producer_partition}"
                    )

        fused_graph = partitioner.fuse_partitions(partitions)
        a, b, c = torch.rand(4), torch.rand(4), torch.rand(4)
        expected = TestNestedGetitemFunctions.forward_nested_getitem_cross_partition(a, b, c)
        result = fused_graph(a, b, c)
        torch.testing.assert_close(expected, result)