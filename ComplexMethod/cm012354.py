def _apply_bucket(self, bucket_info: CollBucket) -> None:
        """
        Apply bucketing transformation.

        Dependencies are added to aug_graph.extra_deps and transferred from old nodes.
        """

        from torch._inductor.fx_passes.bucketing import (
            is_all_reduce_tensor,
            merge_all_gather_bucket,
            merge_all_reduce_bucket,
            merge_reduce_scatter_bucket,
        )

        bucket = bucket_info.collectives

        # Collect old nodes BEFORE they're erased
        old_starts = list(bucket)
        old_waits = [self.collective_info[n].wait_node for n in bucket]

        fused_convert_dtypes = []
        for n in old_starts:
            if has_mergeable_all_gather_convert_dtype(n):
                fused_convert_dtypes.append(n.args[0])

        # Find where to place the bucketed operations
        next_node = bucket[0]
        while next_node in bucket:
            next_node = next_node.next

        # Don't use wait_insertion_point - let merge functions place waits naturally
        # The wait_insertion_point feature tries to move waits to a specific location,
        # but this can cause issues when that location is one of the nodes being erased
        # Create bucketed collective (this will erase old nodes)
        if is_all_gather(bucket[0]):
            new_nodes, replacements = merge_all_gather_bucket(
                self.graph,
                bucket,
                insert_before=next_node,
                mode=self.bucket_mode,
            )
        elif is_all_reduce_tensor(bucket[0]):
            new_nodes, replacements = merge_all_reduce_bucket(
                self.graph,
                bucket,
                mode=self.bucket_mode,
                insert_before=next_node,
            )
        else:
            assert is_reduce_scatter(bucket[0])
            new_nodes, replacements = merge_reduce_scatter_bucket(
                self.graph,
                bucket,
                insert_before=next_node,
                mode=self.bucket_mode,
            )

        # Identify the new wait(s) and their collective start in a single pass
        wait_to_start = {
            n: start
            for n in new_nodes
            if (start := _get_collective_node_from_wait(n)) is not None
        }
        new_waits = list(wait_to_start)

        # Create mapping of all erased nodes to their replacements
        erased_to_new: dict[fx.Node, fx.Node | None] = {}
        new_start = wait_to_start[new_waits[0]]
        if len(new_waits) == 1:
            # Standard bucketing: single start + single wait
            new_wait = new_waits[0]
            for old_start in old_starts:
                erased_to_new[old_start] = new_start
            for old_wait in old_waits:
                erased_to_new[old_wait] = new_wait
        else:
            # Coalesced bucketing: single start + N waits (one per original tensor)
            assert len(new_waits) == len(old_waits)
            for old_start in old_starts:
                erased_to_new[old_start] = new_start
            erased_to_new.update(dict(zip(old_waits, new_waits)))

        # Handle convert_element_type nodes that were fused and erased
        # The bucketed operation may have a _pre_bucket op that handles dtype conversion
        if fused_convert_dtypes:
            # In custom_ops mode, the _pre_bucket_all_gather node handles dtype conversion
            # In default mode, convert nodes are just erased — map them to new_start
            new_convert_dtypes_node = new_start.kwargs.get("out")
            if (
                isinstance(new_convert_dtypes_node, fx.Node)
                and new_convert_dtypes_node.target
                == torch.ops.bucketing._pre_bucket_all_gather.default
            ):
                replacement = new_convert_dtypes_node
            else:
                replacement = new_start

            for n in fused_convert_dtypes:
                erased_to_new[n] = replacement

        # Transfer all dependencies from old nodes to new nodes
        self.aug_graph.transfer_erased_node_deps(erased_to_new)