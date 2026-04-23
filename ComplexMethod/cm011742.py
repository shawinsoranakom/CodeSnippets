def _score_fusion_memory_by_buffer_overlap(
        self, node1: BaseSchedulerNode, node2: BaseSchedulerNode
    ) -> int:
        """
        Score fusion based on buffer name overlap when exact dep matching fails.

        This handles the split/cat fusion case where nodes read from the same buffer
        but at different indices (e.g., different slices from a split operation).

        Scoring logic:
        - If nodes read from exactly the same buffers: high bonus (encourages fusion)
        - For common buffers: score based on overlap ratio
          - overlap_ratio = common_buffer_size /
            max(node1_total_reads, node2_total_reads)
          - If overlap_ratio > threshold (e.g., 0.5): give proportional score
          - If overlap_ratio < threshold: minimal/no score (not worth fusing)

        Note on dynamic shapes:
        - When deps have unbacked symbols (dynamic shapes), dep_size_hint returns 0
        - In this case, we use count * 10 as a proxy for size
        - This ensures fusion still works for models with dynamic batch sizes

        Note on multiple deps from same buffer:
        - A node may have multiple MemoryDep entries for the same buffer name
          (e.g., 4 split reads from arg0_1 at different indices)
        - We sum ALL dep sizes for each buffer, not just take max
        - This ensures overlap ratio is calculated correctly when nodes read
          multiple slices from the same underlying buffer
        """
        # Fallback size when dep_size_hint returns 0 (e.g., unbacked symbols)
        FALLBACK_DEP_SIZE = 10

        def get_dep_size(dep: Dep) -> int:
            size = self.dep_size_hint(dep)
            return size if size > 0 else FALLBACK_DEP_SIZE

        node1_read_names = OrderedSet(dep.name for dep in node1.read_writes.reads)
        node2_read_names = OrderedSet(dep.name for dep in node2.read_writes.reads)

        # Early exit if no common buffer names
        common_names = node1_read_names & node2_read_names

        if not common_names:
            return 0

        # Calculate total read sizes for each node (sum of ALL deps)
        node1_total_read_size = sum(
            get_dep_size(dep) for dep in node1.read_writes.reads
        )
        node2_total_read_size = sum(
            get_dep_size(dep) for dep in node2.read_writes.reads
        )

        max_total_read_size = max(node1_total_read_size, node2_total_read_size)
        if max_total_read_size == 0:
            return 0

        # Calculate total reads from common buffers for each node
        # Sum ALL deps for each common buffer name
        # (handles multiple reads from same buffer)
        node1_common_read_size = sum(
            get_dep_size(dep)
            for dep in node1.read_writes.reads
            if dep.name in common_names
        )
        node2_common_read_size = sum(
            get_dep_size(dep)
            for dep in node2.read_writes.reads
            if dep.name in common_names
        )

        # Use max of the two as the common buffer size estimate
        # This represents how much data is being read from shared buffers
        common_read_buffer_size = max(node1_common_read_size, node2_common_read_size)

        # Calculate overlap ratio
        overlap_ratio = common_read_buffer_size / max_total_read_size
        # Scale score by overlap ratio and common buffer size
        # Higher overlap = higher score
        # Larger common buffer = higher score (more cache benefit)
        return (
            common_read_buffer_size if overlap_ratio >= config.min_overlap_ratio else 0
        )