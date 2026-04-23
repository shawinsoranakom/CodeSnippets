def bucket_collectives(self) -> None:
        """Run the full bucketing and dep application flow.

        Order is important:
        1. Bucketing - merge collectives into buckets
        2. Inline fusions - expand call_module back to original nodes
        3. Transfer deps - move deps from erased nodes to their replacements
        4. Add control deps - apply effect tokens and topo sort

        Steps 2-3 MUST happen before step 4, because control deps need to
        reference the final inlined nodes, not the erased fusion modules.
        """
        # Step 1: Bucket collectives
        all_buckets: list[CollBucket] | None = None
        if self.collective_bucketing:
            all_buckets = self._bucket_collectives_impl()

        # Step 2: Inline fusion regions (expand call_module -> original nodes)
        replaced: dict[fx.Node, fx.Node | None] = {}
        if self.region_of:
            from torch._inductor.fx_passes.fusion_regions import expand_fusion_regions

            gm = self.graph.owning_module
            replaced = expand_fusion_regions(gm, self.region_of)

        # Step 3: Transfer deps from erased fusion modules to inlined nodes
        if replaced:
            self.aug_graph.transfer_erased_node_deps(replaced)

        # Step 4: Add control deps (MUST be after inline + transfer)
        self._apply_deps_and_effect_tokens()
        self.graph.lint()

        if (
            overlap_scheduling_log.isEnabledFor(logging.DEBUG)
            and all_buckets is not None
        ):
            log_strs: list[str] = []
            stats_num_buckets_per_key = defaultdict(int)
            stats_num_bucketed_collectives_per_key = defaultdict(int)
            stats_num_total_collectives_per_key = defaultdict(int)

            def _bucket_key(node):
                return get_full_bucket_key(node, self.bucket_mode)

            for start, info in self.collective_info.items():
                stats_num_total_collectives_per_key[_bucket_key(start)] += 1

            for i, bucket in enumerate(all_buckets):
                bucket_n = len(bucket.collectives)
                if bucket_n == 0:
                    continue
                node = bucket.collectives[0]
                key = _bucket_key(node)
                stats_num_buckets_per_key[key] += 1
                stats_num_bucketed_collectives_per_key[key] += bucket_n
                log_strs.append(f"bucket[{i}] key:{key} len:{bucket_n}:{bucket}")
                for coll in bucket.collectives:
                    info = self.collective_info[coll]
                    hns = info.hiding_nodes
                    log_strs.append(f"coll:{coll} hiding_nodes:{hns}")

            bucket_log_strs: list[str] = []
            for key, num_buckets in stats_num_buckets_per_key.items():
                num_colls = stats_num_bucketed_collectives_per_key[key]
                bucket_log_strs.append(
                    f"bucket key stats {key}: {num_colls} in {num_buckets}"
                    f" buckets of total:{stats_num_total_collectives_per_key[key]}"
                )
            bucket_log_strs.append("")
            # Add stats to the beginning
            log_strs[:0] = bucket_log_strs
            bucket_logs = "\n".join(log_strs)
            trace_structured(
                "artifact",
                metadata_fn=lambda: {
                    "name": "inductor_fx_passes_overlap_bucketing",
                    "encoding": "string",
                },
                payload_fn=lambda: bucket_logs,
            )