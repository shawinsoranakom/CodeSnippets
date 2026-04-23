def get_comm_tensor_size(func, res, args, kwargs) -> int:  # type: ignore[no-untyped-def]
        """Compute the communication tensor size, except for `wait_tensor`, `barrier`, and `monitored_barrier`."""
        if func in CollectiveOp.COMM_TENSOR_ARG_0:
            return CollectiveOp.sum_tensors(args[0])
        if func in CollectiveOp.COMM_TENSOR_ARG_1:
            return CollectiveOp.sum_tensors(args[1])
        if func in CollectiveOp.COMM_TENSOR_ARG_RES:
            return res.untyped_storage().nbytes()
        if func in CollectiveOp.COMM_TENSOR_SINGLE_UNTYPED_STORAGE:
            return args[0].untyped_storage().nbytes()
        if func is c10d._reduce_scatter_base_.default:
            return args[1].untyped_storage().nbytes()
        if func is c10d.alltoall_.default:
            # TODO(@sanketpurandare) - Confirm size computation
            return max(
                CollectiveOp.sum_tensors(args[0]), CollectiveOp.sum_tensors(args[1])
            )
        if func is c10d.alltoall_base_.default:
            # TODO(@sanketpurandare) - Confirm size computation
            return max(
                args[0].untyped_storage().nbytes(), args[1].untyped_storage().nbytes()
            )
        if func == _c10d_functional.all_gather_into_tensor_out.default:
            return args[-1].untyped_storage().nbytes()
        if func in CollectiveOp.COMM_TENSOR_RES_SUM:
            return CollectiveOp.sum_tensors(res)
        if func in CollectiveOp.COMM_TENSOR_ARG_0_AND_RES:
            # TODO(@sanketpurandare) - Confirm size computation
            return args[0].untyped_storage().nbytes() + res.untyped_storage().nbytes()
        if func is _c10d_functional.batch_p2p_ops.default:
            return CollectiveOp.sum_tensors(args[3])
        raise TypeError(f"Unknown function: {func} in {collective_ops}")