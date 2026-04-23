def fusion_prevent_too_many_reads_and_writes(
        self, node1: BaseSchedulerNode, node2: BaseSchedulerNode, threshold: int
    ) -> bool:
        # After fusion, we need to calculate the unique I/O buffers
        # accounting for buffers that become internal (removed through fusion)

        # Get all nodes that will be in the fused node
        fused_node_names = OrderedSet(
            [node.get_name() for node in node1.get_nodes()]
            + [node.get_name() for node in node2.get_nodes()]
        )

        # Calculate node2 reads that can be removed through fusion,
        # i.e. node2 reads that are outputs of node1
        node1_write_names = OrderedSet(dep.name for dep in node1.read_writes.writes)
        node2_read_names = OrderedSet(dep.name for dep in node2.read_writes.reads)
        reads_removed_through_fusion = node2_read_names & node1_write_names

        # Calculate node1 writes that can be removed through fusion,
        # i.e. node1 writes that are only read by node2
        writes_removed_through_fusion: OrderedSet[str] = OrderedSet()
        for write_dep in node1.read_writes.writes:
            if self.can_buffer_be_removed_through_fusion(
                write_dep.name, fused_node_names
            ):
                writes_removed_through_fusion.add(write_dep.name)

        # Get all unique reads (union of both nodes' reads)
        all_read_names = OrderedSet(
            dep.name for dep in node1.read_writes.reads
        ) | OrderedSet(dep.name for dep in node2.read_writes.reads)

        # Get all unique writes (union of both nodes' writes)
        all_write_names = OrderedSet(
            dep.name for dep in node1.read_writes.writes
        ) | OrderedSet(dep.name for dep in node2.read_writes.writes)

        # Remove reads that become internal
        unique_reads = all_read_names - reads_removed_through_fusion

        # Remove writes that become internal
        unique_writes = all_write_names - writes_removed_through_fusion

        # Get all unique buffer names (reads and writes combined, but no double counting)
        unique_io_buffers = unique_reads | unique_writes

        return len(unique_io_buffers) > threshold