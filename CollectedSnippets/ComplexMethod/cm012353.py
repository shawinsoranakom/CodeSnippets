def _has_ancestor_conflicts(
        self, bucket_info: CollBucket, candidate: fx.Node
    ) -> bool:
        """
        Check if candidate has ancestor conflicts with bucket collectives.
        Returns True if there are conflicts.
        """
        candidate_info = self.collective_info[candidate]
        candidate_wait = candidate_info.wait_node

        for coll in bucket_info.collectives:
            if (
                coll in self.node_ancestors[candidate]
                or candidate in self.node_ancestors[coll]
            ):
                return True

            # Check if waits are ancestors of each other
            coll_wait = self.collective_info[coll].wait_node
            if (
                coll_wait in self.node_ancestors[candidate_wait]
                or candidate_wait in self.node_ancestors[coll_wait]
            ):
                return True

            # Check if existing hiding node conflicts with candidate wait
            for old_hiding_node in self.collective_info[coll].hiding_nodes:
                if candidate_wait in self.node_ancestors[old_hiding_node]:
                    return True

            # Check if candidate hiding node conflicts with existing wait
            for new_hiding_node in candidate_info.hiding_nodes:
                if coll_wait in self.node_ancestors[new_hiding_node]:
                    return True

        return False