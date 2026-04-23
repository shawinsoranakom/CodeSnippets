def hook_with_zero_fn(
        state: Any,
        bucket: dist.GradBucket,
    ) -> torch.futures.Future[torch.Tensor]:
        r"""
        Return :class:`Future` that runs the optimizer step if this corresponds to the last gradient bucket.

        Perform equivalent of :class:`ZeroRedundancyOptimizer` :meth:`step` if ``bucket`` is last gradient bucket.
        The function gives a gradient bucket tensor and
        performs additional computation on the iteration that
        the :class:`DistributedDataParallel` buckets are rebuilt to collect
        information used to implement the modified hook.

        Arguments:
            state (Any): any state for the hook.
            bucket (dist.GradBucket): the :class:`DistributedDataParallel`
                gradient bucket.
        """
        fut = hook(state, bucket)
        _hook_with_zero_step_setup(ddp_ref, zero, bucket)
        if zero._overlap_info.status != _OverlapStatus.INITIALIZED:
            return fut

        overlap_info = zero._overlap_info
        bucket_index = bucket.index()
        rank = zero.global_rank

        if overlap_info.status != _OverlapStatus.INITIALIZED:
            raise AssertionError
        if len(overlap_info.assigned_ranks_per_bucket) <= bucket_index:
            raise AssertionError("`assigned_ranks_per_bucket` is not fully constructed")
        assigned_to_bucket = (
            rank in overlap_info.assigned_ranks_per_bucket[bucket_index]
        )

        # Save the bucket reference and all-reduce future for the final bucket
        if assigned_to_bucket:
            overlap_info.bucket_index_to_bucket[bucket_index] = bucket
            overlap_info.bucket_index_to_future[bucket_index] = fut

        # Check that buckets are indexed incrementally starting from 0 in the
        # order of their autograd hooks firing
        if len(overlap_info.bucket_indices_seen) > 0:
            if overlap_info.bucket_indices_seen[-1] != bucket_index - 1:
                raise AssertionError("Bucket indices are not in incremental order")
        else:
            if bucket_index != 0:
                raise AssertionError("Bucket indices do not start from 0")
        overlap_info.bucket_indices_seen.append(bucket_index)

        # Directly return the future without any optimizer computation if this
        # is not the last bucket
        num_buckets = len(overlap_info.params_per_bucket)
        is_last_bucket = bucket_index == num_buckets - 1
        if not is_last_bucket:
            return fut

        # Perform partial optimizer step on all buckets after the final
        # bucket has been computed
        # NOTE: This should not be chained as a callback to the last bucket's
        # all-reduce future since that would add synchronization that delays
        # all optimizer computation to wait for that last all-reduce
        for bucket_index in range(num_buckets):
            assigned_ranks = overlap_info.assigned_ranks_per_bucket[bucket_index]
            if rank in assigned_ranks:
                # Wait on the bucket's all-reduce future to ensure correct
                # gradients
                if bucket_index not in overlap_info.bucket_index_to_future:
                    raise AssertionError(
                        f"All-reduce future for bucket {bucket_index} not saved "
                        f"on rank {rank}"
                    )
                allreduce_future = overlap_info.bucket_index_to_future[bucket_index]
                allreduce_future.wait()

                # Perform the partial optimizer step
                curr_bucket = overlap_info.bucket_index_to_bucket[bucket_index]
                _perform_local_step(curr_bucket, zero, rank)

            _broadcast_bucket(bucket_index, zero)

        # Ensure that all parameter updates are finished before the
        # next forward pass
        overlap_info.wait_for_broadcasts()
        overlap_info.clear_per_iter_info()

        return fut