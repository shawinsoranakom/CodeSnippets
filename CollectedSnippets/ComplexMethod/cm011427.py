def _dispatch_fast_path_python_tail(
        self,
        op_call: torch._ops.OpOverload,
        args: tuple[object, ...],
        kwargs: dict[str, object],
        compute_mesh: DeviceMesh,
        output_sharding: OutputSharding,
        local_results: object,
        participating: bool,
        is_inplace_op: bool,
        is_out_variant_op: bool,
    ) -> object:
        """
        Tail of main dispatching logic, called from C++ fast path.
        """

        # Record output placements for debugging
        debug_mode = get_active_debug_mode()
        if debug_mode is not None and output_sharding.output_spec is not None:
            debug_mode.record_output_placements(output_sharding.output_spec)

        if output_sharding.output_spec is None:
            if op_call == aten.equal.default:
                # The output of the equal op is a bool, by converting it into a
                # a single value tensor, we can use all-reduce with min reduce op
                # to simulate logical and.
                if not (local_results is None or isinstance(local_results, bool)):
                    raise AssertionError
                r = torch.tensor(
                    int(local_results) if local_results is not None else 1,
                    device=compute_mesh.device_type,
                )
                dist.all_reduce(r, op=dist.ReduceOp.MIN)
                local_results = bool(r.item())

        if is_inplace_op:
            # inplace op should return self instead of re-wrapping
            if output_sharding.output_spec is not None:
                output_spec = output_sharding.output_spec
                if not isinstance(output_spec, DTensorSpec):
                    raise AssertionError
                if not isinstance(args[0], dtensor.DTensor):
                    raise AssertionError

                # Fast path: placements unchanged (common case: add_, mul_, etc.)
                if args[0]._spec.placements == output_spec.placements:
                    return args[0]

                # Placement reindexed (e.g. squeeze_ removing a non-sharded
                # dim: Shard(1) → Shard(0)). No redistribution — the local
                # tensor data is unchanged, only dim indices shift.
                # strict_view=True in sharding prop prevents the illegal
                # case (squeezing a sharded dim) from reaching here.
                args[0]._spec = output_spec
                return return_and_correct_aliasing(op_call, args, kwargs, args[0])
            else:
                return None
        elif is_out_variant_op:
            # out variant could possibly have multiple out args (i.e. lu_unpack.out)
            output_specs = (
                (output_sharding.output_spec,)
                if not isinstance(output_sharding.output_spec, tuple)
                else output_sharding.output_spec
            )
            out_dts = []
            spec_idx = 0
            for argument in op_call._schema.arguments:
                if argument.is_out:
                    out_dt = cast(dtensor.DTensor, kwargs[argument.name])
                    out_dt._spec = cast(DTensorSpec, output_specs[spec_idx])
                    out_dts.append(out_dt)
                    spec_idx += 1

            if len(out_dts) < 1:
                raise AssertionError("out variant should have at least one out arg")
            return tuple(out_dts) if len(out_dts) > 1 else out_dts[0]
        else:
            if op_call != aten.equal.default:
                raise AssertionError(op_call)
            ret = self.wrap(local_results, output_sharding.output_spec)  # type: ignore[possibly-undefined]
            if participating and op_call._schema._is_view_op():
                return return_and_correct_aliasing(op_call, args, kwargs, ret)
            else:
                return ret