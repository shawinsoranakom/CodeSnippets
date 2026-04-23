def _test_all_reduce_helper(
            self,
            group,
            group_id,
            rank,
            op,
            master_value,
            worker_value,
            expected_value,
            cuda=False,
            rank_to_GPU=None,
            dtype=torch.float,
            async_op=False,
        ):
            for src in group:
                curr_value = master_value if rank == src else worker_value

                tensor = _build_tensor(src + 1, dtype=dtype).fill_(curr_value)
                if cuda:
                    tensor = tensor.cuda(rank_to_GPU[rank][0])
                if tensor.dtype == torch.complex64:
                    tensor_shapes = [torch.view_as_real(tensor).shape]
                else:
                    tensor_shapes = [tensor.shape]
                self.call_dist_op(
                    ":all_reduce",
                    async_op,
                    dist.all_reduce,
                    tensor,
                    op,
                    group_id,
                    async_op=async_op,
                    tensor_shapes=tensor_shapes,
                )
                # Currently, only Gloo backend has profiling tested with CUDA enabled.
                # Only run cuda profiling test for one rank to speed up since
                # running with different src_rank does not affect the correctness.
                if (
                    src == 0
                    and cuda
                    and dist.get_backend() in CUDA_PROFILING_SUPPORTED_BACKENDS
                ):
                    self.call_dist_op(
                        ":all_reduce",
                        async_op,
                        dist.all_reduce,
                        tensor,
                        op,
                        group_id,
                        async_op=async_op,
                        profile_cuda=True,
                        tensor_shapes=tensor_shapes,
                    )

            self._barrier()