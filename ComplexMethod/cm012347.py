def _bucket_collectives_impl(self) -> list[CollBucket]:
        """Find and apply bucket transformations for collectives."""
        pg_collectives: dict[str, OrderedSet[fx.Node]] = defaultdict(OrderedSet)
        internode_pgs = self.identify_internode_group_names()

        for start in self.collective_info:
            pg = get_group_name(start)
            pg_collectives[pg].add(start)

        all_buckets: list[CollBucket] = []
        for pg, collectives in pg_collectives.items():
            if self.bucket_only_internode_comms and pg not in internode_pgs:
                continue

            # Populate node_to_event for this PG's timeline
            self._populate_node_to_event(pg)

            grouped_collectives: dict[object, OrderedSet[fx.Node]] = defaultdict(
                OrderedSet
            )
            for start in collectives:
                key = get_full_bucket_key(start, self.bucket_mode)
                if key[1] is not None:
                    grouped_collectives[key].add(start)

            for key, collective_group in grouped_collectives.items():
                bucket_log.debug(
                    "bucketing collective group with key %s: %s",
                    key,
                    [n.name for n in collective_group],
                )
                buckets = self._find_buckets(collective_group, internode_pgs)
                all_buckets.extend(buckets)

        for coll_bucket in all_buckets:
            if len(coll_bucket.collectives) <= 1:
                continue

            counters["inductor"]["collective_buckets"] += 1
            self._apply_bucket(coll_bucket)
        return all_buckets