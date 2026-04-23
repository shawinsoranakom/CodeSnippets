def fuse(
        cls, producer: BaseSchedulerNode, consumer: BaseSchedulerNode
    ) -> ForeachKernelSchedulerNode:
        assert producer.is_foreach() or consumer.is_foreach()
        if producer.is_foreach():
            producer = typing.cast(ForeachKernelSchedulerNode, producer)
            use_custom_partition_algo = producer.use_custom_partition_algo
            enable_autotune = producer.enable_autotune
        else:
            consumer = typing.cast(ForeachKernelSchedulerNode, consumer)
            use_custom_partition_algo = consumer.use_custom_partition_algo
            enable_autotune = consumer.enable_autotune
        prev_node_1 = None
        prev_node_2 = None
        fused_nodes: list[BaseSchedulerNode]
        if producer.is_foreach() and consumer.is_foreach():
            producer = typing.cast(ForeachKernelSchedulerNode, producer)
            consumer = typing.cast(ForeachKernelSchedulerNode, consumer)
            fused_nodes = [
                FusedSchedulerNode.fuse(l, r)
                for l, r in zip(producer.snodes, consumer.snodes)
            ]
        elif producer.is_foreach():
            producer = typing.cast(ForeachKernelSchedulerNode, producer)
            producer_subnode = producer.get_producer_subnode_for(consumer)
            fused_nodes = []
            prev_node_1 = producer
            prev_node_2 = None
            for node in producer.snodes:
                if node is producer_subnode:
                    new_node = FusedSchedulerNode.fuse(node, consumer)
                    prev_node_2 = new_node
                    fused_nodes.append(new_node)
                else:
                    fused_nodes.append(node)

        elif consumer.is_foreach():
            consumer = typing.cast(ForeachKernelSchedulerNode, consumer)
            consumer_subnode = consumer.get_consumer_subnode_for(producer)
            fused_nodes = []
            prev_node_1 = consumer
            prev_node_2 = None

            for node in consumer.snodes:
                if node is consumer_subnode:
                    new_node = FusedSchedulerNode.fuse(producer, node)
                    prev_node_2 = new_node
                    fused_nodes.append(new_node)
                else:
                    fused_nodes.append(node)
        else:
            raise AssertionError(
                "At least one node passed to ForeachKernelSchedulerNode.fuse should be a foreach node"
            )

        return cls(
            producer.scheduler,
            fused_nodes,
            use_custom_partition_algo=use_custom_partition_algo,
            prev_node_1=prev_node_1,
            prev_node_2=prev_node_2,
            enable_autotune=enable_autotune,
        )