def __torch_dispatch__(
        self,
        func: Any,
        types: tuple[Any, ...],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        if kwargs is None:
            kwargs = {}

        flat_args, args_spec = pytree.tree_flatten((args, kwargs))

        # Find all LocalTensor arguments to determine ranks
        local_tensors = [a for a in flat_args if isinstance(a, LocalTensor)]

        # Check for unrecognized tensor subclasses (but allow regular tensors and scalars)
        has_unrecognized_types = _check_for_subclass(flat_args)
        if has_unrecognized_types:
            unrecognized_types = [
                type(x) for x in flat_args if _check_for_subclass_arg(x)
            ]
            not_implemented_log.debug(
                "LocalTensorMode unrecognized subclass(es): %s", unrecognized_types
            )
            return NotImplemented

        # Factory functions convert into LocalTensor, so we don't have to
        # transmute a Tensor into a LocalTensor if mutation happens...
        # But if you do an operation on a Tensor, do NOT wrap it into a
        # LocalTensor.  This helps prevent accidents when you're doing Tensor
        # operations on the inner non-wrapped tensors.
        if not local_tensors:
            if self._disable or any(isinstance(a, Tensor) for a in flat_args):
                return func(*args, **kwargs)

        # For LocalTensors, verify they have compatible ranks
        for a in flat_args:
            if isinstance(a, LocalTensor):
                if a._ranks > self.ranks:
                    raise AssertionError(
                        f"Input LocalTensor {a} must be configured for a "
                        f"subset of the LocalTensorMode ranks {self.ranks}"
                    )

        if func.overloadpacket == torch.ops.aten.dim:
            return len(args[0]._size)
        if func.overloadpacket == torch.ops.aten.sym_size:
            return tuple(args[0]._size)

        if func.namespace == "c10d":
            if func is torch.ops.c10d.allreduce_.default:
                return _c10d._local_all_reduce_(*args, **kwargs)
            elif func is torch.ops.c10d.allreduce_coalesced_.default:
                return _c10d._local_allreduce_coalesced_(*args, **kwargs)
            elif func is torch.ops.c10d.reduce_scatter_tensor_coalesced_.default:
                return _c10d._local_reduce_scatter_tensor_coalesced_(*args, **kwargs)
            elif func is torch.ops.c10d.scatter_.default:
                return _c10d._local_scatter_(*args, **kwargs)
            elif func is torch.ops.c10d.broadcast_.default:
                return _c10d._local_broadcast_(*args, **kwargs)
            elif func is torch.ops.c10d.allgather_.default:
                return _c10d._local_all_gather_(*args, **kwargs)
            elif func is torch.ops.c10d.allgather_into_tensor_coalesced_.default:
                return _c10d._local_allgather_into_tensor_coalesced_(*args, **kwargs)
            elif func is torch.ops.c10d._allgather_base_.default:
                return _c10d._local_allgather_base_(*args, **kwargs)
            elif func is torch.ops.c10d._reduce_scatter_base_.default:
                return _c10d._local_reduce_scatter_base_(*args, **kwargs)
            elif func is torch.ops.c10d.gather_.default:
                return _c10d._local_gather_(*args, **kwargs)
            elif func is torch.ops.c10d.alltoall_.default:
                return _c10d._local_alltoall_(*args, **kwargs)
            elif func is torch.ops.c10d.alltoall_base_.default:
                return _c10d._local_alltoall_base_(*args, **kwargs)
            elif func is torch.ops.c10d.barrier.default:
                return _c10d._local_barrier(*args, **kwargs)
            elif func is torch.ops.c10d.monitored_barrier_.default:
                return _c10d._local_monitored_barrier_(*args, **kwargs)
            elif func is torch.ops.c10d.send.default:
                return _c10d._local_send(*args, **kwargs)
            elif func is torch.ops.c10d.recv_.default:
                return _c10d._local_recv_(*args, **kwargs)
            elif func is torch.ops.c10d.recv_any_source_.default:
                return _c10d._local_recv_any_source_(*args, **kwargs)
            raise NotImplementedError(f"{func} not implemented")

        if func.namespace == "_c10d_functional" or func.namespace == "_dtensor":
            if func is torch.ops._dtensor.shard_dim_alltoall.default:
                return _c10d._local_functional_shard_dim_alltoall(*args, **kwargs)
            elif func is torch.ops._c10d_functional.all_gather_into_tensor.default:
                return _c10d._local_functional_all_gather_into_tensor(*args, **kwargs)
            elif func is torch.ops._c10d_functional.reduce_scatter_tensor.default:
                return _c10d._local_functional_reduce_scatter_tensor(*args, **kwargs)
            elif func is torch.ops._c10d_functional.all_to_all_single.default:
                return _c10d._local_functional_all_to_all_single(*args, **kwargs)
            else:
                with LocalTensorMode(self.ranks):
                    return func._op_dk(
                        DispatchKey.CompositeExplicitAutograd, *args, **kwargs
                    )

        if func.namespace == "profiler":
            return func(*args, **kwargs)

        if func.namespace == "_c10d_functional_autograd":
            raise NotImplementedError(f"{func} not implemented")

        if func.namespace == "symm_mem":
            raise NotImplementedError(f"{func} not implemented")

        return _for_each_rank_run_func(func, self.ranks, args, kwargs, alias=True)