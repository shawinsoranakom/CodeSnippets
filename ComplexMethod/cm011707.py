def can_fuse_with(self, other: BaseSchedulerNode):
        # Limit tl.load() count in the fused RSPLIT loop to avoid register
        # spills. See https://github.com/pytorch/pytorch/issues/179423
        max_reads = config.triton.mix_order_reduction_max_reads
        if max_reads > 0:
            all_reads: OrderedSet[str] = OrderedSet()
            for sn in itertools.chain(self.get_nodes(), other.get_nodes()):
                for dep in sn.read_writes.reads:
                    if isinstance(dep, MemoryDep):
                        all_reads.add(dep.name)
            if len(all_reads) > max_reads:
                # pyrefly: ignore [bad-assignment]
                metrics.rejected_mix_order_reduction_fusion += 1
                return False
        if not isinstance(other, FusedMixOrderReductions):
            return self.sub_node_can_fuse(
                self.node1, other, (self.node2,)
            ) or self.sub_node_can_fuse(self.node2, other, (self.node1,))
        else:
            # pass empty tuple for the second since the producer/consumer relationship has
            # already been checked in the first call
            return self.sub_node_can_fuse(
                self.node1, other.node1, (self.node2, other.node2)
            ) and self.sub_node_can_fuse(self.node2, other.node2, tuple())