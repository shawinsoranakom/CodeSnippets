def _bucket_assignments_per_rank(self) -> list[dict[int, _DDPBucketAssignment]]:
        r"""
        Return DDP bucket parameters assigned per rank.

        :class:`list` of length world size consisting of :class:`dict` s
        mapping bucket indices to :class:`_DDPBucketAssignment` s for each
        rank.
        """
        if not self._overlap_with_ddp:
            raise AssertionError(
                "`_bucket_assignments_per_rank` only be used if `overlap_with_ddp=True`"
            )
        if len(self._bucket_assignments_per_rank_cache) > 0:
            return self._bucket_assignments_per_rank_cache

        overlap_info = self._overlap_info
        if overlap_info.status != _OverlapStatus.INITIALIZED:
            raise AssertionError

        self._bucket_assignments_per_rank_cache = [{} for _ in range(self.world_size)]
        params_per_bucket = overlap_info.params_per_bucket

        if overlap_info.shard_buckets:
            # Define the assignment threshold to approximate uniformity
            if overlap_info.total_size is None:
                raise AssertionError("`total_size` was not computed")
            threshold = overlap_info.total_size / self.world_size  # type: ignore[operator]
            size_per_rank = [0 for _ in range(self.world_size)]

        num_buckets = len(params_per_bucket)
        overlap_info.assigned_ranks_per_bucket = [set() for _ in range(num_buckets)]
        assigned_ranks_per_bucket = overlap_info.assigned_ranks_per_bucket
        if not overlap_info.shard_buckets:
            # Assign each DDP bucket entirely to a single rank
            for bucket_index, bucket_params in enumerate(params_per_bucket):
                if len(bucket_params) <= 0:
                    raise AssertionError("Empty bucket")
                assigned_rank = self._get_assigned_rank(bucket_index)
                self._assign_bucket_subset_to_rank(
                    bucket_index,
                    bucket_params,
                    0,
                    assigned_rank,
                    assigned_ranks_per_bucket,
                )
        else:
            # Assign each DDP bucket to possibly multiple ranks
            # Specifically, sort the DDP buckets by increasing size, and for
            # each bucket, iteratively assign the maximal unassigned subset
            # with size less than `threshold` to the rank with the least total
            # size so far -- each such assignment is represented by a
            # `_DDPBucketAssignment` instance and only contains parameters from
            # a single DDP bucket
            params_per_bucket_enum = sorted(
                enumerate(params_per_bucket), key=lambda x: sum(p.numel() for p in x[1])
            )
            for bucket_index, bucket_params in params_per_bucket_enum:
                if len(bucket_params) <= 0:
                    raise AssertionError("Empty bucket")
                bucket_offset = 0
                assignment_size = 0
                for param_index, param in enumerate(bucket_params):
                    param_numel = param.numel()
                    if (
                        # pyrefly: ignore [unbound-name]
                        assignment_size + param_numel >= threshold
                        and param_index > bucket_offset
                    ):
                        assigned_rank = self._get_min_index(
                            # pyrefly: ignore [unbound-name]
                            size_per_rank,
                            assigned_ranks_per_bucket[bucket_index],
                        )
                        # Include up to but not including the parameter that
                        # exceeded the threshold
                        self._assign_bucket_subset_to_rank(
                            bucket_index,
                            bucket_params[bucket_offset:param_index],
                            bucket_offset,
                            assigned_rank,
                            assigned_ranks_per_bucket,
                        )
                        # pyrefly: ignore [unbound-name]
                        size_per_rank[assigned_rank] += assignment_size
                        bucket_offset = param_index
                        assignment_size = 0
                    assignment_size += param_numel
                # Assign the remainder of the bucket so that no assignment
                # spans across two buckets
                assigned_rank = self._get_min_index(
                    # pyrefly: ignore [unbound-name]
                    size_per_rank,
                    assigned_ranks_per_bucket[bucket_index],
                )
                self._assign_bucket_subset_to_rank(
                    bucket_index,
                    bucket_params[bucket_offset:],
                    bucket_offset,
                    assigned_rank,
                    assigned_ranks_per_bucket,
                )
                # pyrefly: ignore [unbound-name]
                size_per_rank[assigned_rank] += assignment_size

        return self._bucket_assignments_per_rank_cache