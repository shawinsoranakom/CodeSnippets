def manual_bucket_collectives(self, nodes: list[fx.Node]) -> None:
        """
        Bucket all all-gather/reduce-scatter nodes from nodes into one all-gather/reduce-scatter.
        """
        # Filter out valid collectives
        collectives = [n for n in nodes if n in self.collective_info]
        if collectives == []:
            return
        grouped_collectives: dict[object, OrderedSet[fx.Node]] = defaultdict(OrderedSet)
        for node in collectives:
            if not (
                is_fsdp_all_gather(node, self.node_ancestors)
                or is_fsdp_reduce_scatter(node)
            ):
                continue
            key = get_full_bucket_key(node, "custom_ops")
            if key is not None:
                grouped_collectives[key].add(node)

        for key, nodes in grouped_collectives.items():  # type: ignore[arg-type]
            self._bucket_group(list(nodes))