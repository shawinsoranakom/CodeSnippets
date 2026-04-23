def reduction(
        self,
        dtype: torch.dtype,
        src_dtype: torch.dtype,
        reduction_type: ReductionType,
        value: CSEVariable | tuple[CSEVariable, ...],
    ) -> CSEVariable | tuple[CSEVariable, ...]:
        """
        codegen reduction of value to Triton according the reduction_type
        """

        def should_upcast(d: torch.dtype | None) -> bool:
            return d is not None and d.is_floating_point and d.itemsize < 4

        def maybe_upcast(value: CSEVariable) -> CSEVariable:
            # Math reductions in small floats are less accurate because the Triton
            # compiler does not automatically promote to FP32 for accumulation.
            # Additionally, max/min reductions do not support FP16/BF16.  Manually
            # promote to FP32 here.
            return (
                ops.to_dtype(value, torch.float32)
                if should_upcast(value.dtype)
                else value
            )

        do_upcast = pytree.tree_any(lambda v: should_upcast(v.dtype), value)
        original_dtype = dtype
        if do_upcast:
            # Only promote FB16/BF16; do not promote other integer/boolean dtypes
            value = pytree.tree_map(maybe_upcast, value)
            src_dtype = torch.float32 if should_upcast(src_dtype) else src_dtype
            dtype = torch.float32 if should_upcast(dtype) else dtype

        assert self.inside_reduction
        masks = OrderedSet(f"{tree.prefix}mask" for tree in self.range_trees)
        self.filter_masks(masks)
        masks = sorted(masks)
        if self._load_mask:
            masks.append(self._load_mask)
        reduction_range_prefix = self.range_trees[-1].prefix[0]

        # When we do native matmtul codegen,
        # we don't want to keep the R0_BLOCK/R1_BLOCK in the accumulator.
        # so instead of naively calling dense_size_str(), we filter out
        # reduction block from accumulator and only keep (Y,X).
        # In bmm (Z,Y,R)x(Z,R,X) case, we also remove z dimension from accumulator
        # because 3d (Z,Y,X) tl.dot is somehow slower than 2d tl.dot.
        # Instead, we force ZBLOCK to be always 1 during autotune.
        dense_size_str: str
        if self.is_native_matmul:
            dense_sizes = self.dense_size_list()
            assert len(dense_sizes) >= 3
            xy_sizes_only = [size for size in dense_sizes if "X" in size or "Y" in size]
            dense_size_str = f"[{', '.join(xy_sizes_only)}]"
            value_shape = tuple(xy_sizes_only)
        else:
            dense_size_str = self.dense_size_str()
            value_shape = tuple(self.dense_size_list())

        # Say we have
        #     tmp0 = ops.constant(1, torch.int64)
        #     tmp1 = ops.reduction(torch.int64, torch.int64, "sum", tmp0)
        # tmp0 in the triton code is either a scalar, or single-element tensor
        # so if we emit tl.sum directly, it will only give 1 instead of RBLOCK * 1
        # To avoid this, we broadcast to the expected shape first.
        value = self._map_tuple_or_scalar(
            lambda v: self.cse.generate(
                self.compute,
                f"tl.broadcast_to({v}, {dense_size_str})",
                dtype=v.dtype,
                shape=value_shape,
            ),
            value,
        )

        logical_index = None
        if reduction_type in ("argmin", "argmax"):
            if isinstance(value, tuple):
                value, logical_index = value

        dim = self.triton_tensor_ndim() - self.num_reduction_dims
        root_op: str

        def final_reduction(
            buffer,
            value: CSEVariable,
            result_type: torch.dtype | None,
        ) -> tuple[str, torch.dtype | None, BlockShapeType]:
            """
            Helper to generate a reduction call, e.g. tl.sum.
            """
            triton_reduction_fn = get_triton_reduction_function(reduction_type)

            value = self.reduction_collapse_dims(buffer, value, dtype)
            if reduction_type == "dot":
                # Native matmul is a special case because accumulator shape is fixed to (Y,X)
                is_bmm = len(self.dense_size_list()) == 4
                assert value.shape is not None
                if is_bmm:
                    result = f"{value}[None,:,:,None]"  # (Y,X) to (Z=1,Y,X,R=1)
                    shape = [1, *value.shape, 1]
                else:
                    result = f"{value}[:,:,None]"  # (Y,X) to (Y,X,R=1)
                    shape = [*value.shape, 1]
            else:
                result, shape = self.reduction_resize_and_shape(  # type: ignore[assignment]
                    f"{triton_reduction_fn}({value}, {dim})", value.shape
                )

            if result_type is not None:
                result = f"{result}.to({self.dtype_to_str(result_type)})"
            else:
                result_type = value.dtype

            return result, result_type, shape

        def final_reduction_define(
            buffer,
            result_var: CSEVariable,
            value: CSEVariable,
            result_type: torch.dtype | None,
        ) -> None:
            """
            Generate a reduction and assign it to an existing variable.
            """
            # pyrefly: ignore [bad-assignment]
            value, _, _ = final_reduction(buffer, value, result_type)
            buffer.splice(f"{result_var} = {value}")

        def final_argreduce(buffer, result_var, value, index):
            value = self.reduction_collapse_dims(buffer, value, dtype)
            index = self.reduction_collapse_dims(buffer, index, dtype)
            buffer.splice(
                f"""\
                {result_var}_val, {result_var}_idx = triton_helpers.{root_op}_with_index({value}, {index}, {dim})
                {result_var} = {self.reduction_resize(f"{result_var}_idx")}
                """
            )

        cache_key = (src_dtype, reduction_type, value)
        if cache_key in self.cse.reduction_cache:
            return self.cse.reduction_cache[cache_key]

        acc_type = triton_acc_type(src_dtype)
        torch_acc_type = upcast_acc_dtype(src_dtype)
        result_shape = list(self.dense_size_list())
        result_shape[dim] = "1"
        result_var: Any = self.cse.newvar(
            dtype=torch_acc_type, shape=tuple(result_shape)
        )
        result_var.mask_vars = OrderedSet(
            var for var in masks if not prefix_is_reduction(var[0])
        )
        cond = " & ".join(masks)

        def where_cond(tval, fval):
            if not cond:
                return tval
            return TritonKernelOverrides.where(cond, tval, fval)

        if self.persistent_reduction:
            default = ir.Reduction.default_value(reduction_type, src_dtype)

            def update_constant_dtype(constant, src_dtype, dst_dtype):
                "update reduction constant mask value to match dst_dtype"

                # int is the only mask which may not fit within lower bitwidth,
                # because float uses inf/-inf
                if src_dtype.is_floating_point or src_dtype == torch.bool:
                    return constant

                if src_dtype == dst_dtype or constant == 0:
                    return constant

                if constant == torch.iinfo(src_dtype).max:
                    return torch.iinfo(dst_dtype).max
                elif constant == torch.iinfo(src_dtype).min:
                    return torch.iinfo(dst_dtype).min
                else:
                    return constant

            def _mask_value(value, default) -> CSEVariable:
                default = update_constant_dtype(default, src_dtype, value.dtype)
                default_str = self._map_tuple_or_scalar(constant_repr, default)

                return self.cse.generate(
                    self.compute,
                    where_cond(value, default_str),
                    dtype=value.dtype,
                    shape=value.shape,
                )

            masked_value: CSEVariable | Sequence[CSEVariable] | None
            if reduction_type == "online_softmax_reduce":
                # Don't generate mask value for online_softmax since we
                # will fallback below
                masked_value = None
            elif isinstance(value, tuple):
                masked_value = [_mask_value(v, d) for v, d in zip(value, default)]  # type: ignore[arg-type]
            elif reduction_type == "dot":
                # Here, we don't perform the masking.
                # Masking w/ where condition in native matmul is handled in ops.dot codegen.
                # Since tl.dot performs reduction within the triton block,
                # masking should happen before the tl.dot is called.
                masked_value = self.cse.generate(self.compute, value, dtype=value.dtype)
            else:
                masked_value = _mask_value(value, default)

            if reduction_type in ("argmax", "argmin"):
                assert isinstance(masked_value, CSEVariable)
                accumulator_dtype = V.kernel.get_index_dtype_as_torch_dtype()
                if logical_index:
                    accumulator_index = f"({str(logical_index)}).to({self.dtype_to_str(accumulator_dtype)})"
                else:
                    accumulator_index = str(
                        self.cse.generate(
                            self.compute,
                            f"tl.broadcast_to({reduction_range_prefix}index, {masked_value}.shape)",
                            dtype=accumulator_dtype,
                            shape=masked_value.shape,
                        )
                    )
                root_op = {"argmax": "max", "argmin": "min"}[reduction_type]
                final_argreduce(
                    self.compute, result_var, masked_value, accumulator_index
                )
                result_var.dtype = accumulator_dtype
            elif reduction_type == "welford_reduce":
                if self.cooperative_reduction:
                    # cooperative reductions require full welford for correctness
                    result_var = self.welford_reduce(
                        result_var, reduction_type, value, where_cond, acc_type, dtype
                    )
                else:
                    # For persistent reductions, don't bother with
                    # welford's algorithm since it uses more registers, and
                    # taking two reductions doesn't increase memory usage.
                    result_var = self.welford_reduce_fallback(dtype, value)
            elif reduction_type == "welford_combine":
                assert isinstance(masked_value, Sequence)
                (mean, m2, weight) = masked_value
                result_var = tuple(
                    self.cse.generate(self.compute, value, dtype=dtype, shape=shape)
                    for value, shape in self._welford(
                        self.compute, mean, m2, weight, dim, dtype
                    )
                )
            elif reduction_type == "online_softmax_reduce":
                # All data is loaded to register anyway, no need to do
                # online softmax
                result_var = self.prepare_softmax_twopass_fallback(dtype, value)
            else:
                assert isinstance(masked_value, CSEVariable)
                _result, _dtype, _shape = final_reduction(
                    self.compute, masked_value, masked_value.dtype
                )
                result_var = self.cse.generate(
                    self.compute, _result, dtype=_dtype, shape=_shape
                )
        else:
            accumulator = self.cse.namedvar(
                f"_{result_var}",
                dtype=torch_acc_type,
                shape=tuple(self.dense_size_list()),
            )
            default = ir.Reduction.default_accumulator(reduction_type, src_dtype)
            default = self._map_tuple_or_scalar(constant_repr, default)
            if not isinstance(default, tuple):
                if reduction_type == "dot":
                    dense_sizes = self.dense_size_list()
                    assert len(dense_sizes) >= 3
                    xy_sizes_only = [
                        size for size in dense_sizes if "X" in size or "Y" in size
                    ]
                    accumulator.shape = tuple(xy_sizes_only)
                    dense_size_str = f"[{', '.join(xy_sizes_only)}]"
                    self.body.writeline(
                        f"{accumulator} = tl.full({dense_size_str}, {default}, {acc_type})"
                    )
                else:
                    self.body.writeline(
                        f"{accumulator} = tl.full({self.dense_size_str()}, {default}, {acc_type})"
                    )

            if reduction_type in ("argmax", "argmin"):
                accumulator_index = f"_{result_var}_index"
                index_dtype = self.features.select_index_dtype()
                self.body.writeline(
                    f"{accumulator_index} = tl.full({self.dense_size_str()}, "
                    f"{torch.iinfo(index_dtype).max}, {self.dtype_to_str(index_dtype)})"
                )
                root_op = {"argmax": "max", "argmin": "min"}[reduction_type]
                # Use logical_index if it was unpacked, otherwise fall back to physical index
                index_var = (
                    f"({str(logical_index)}).to({self.dtype_to_str(index_dtype)})"
                    if logical_index is not None
                    else f"{reduction_range_prefix}index"
                )
                self.compute.splice(
                    f"""\
                {accumulator}_next, {accumulator_index}_next = triton_helpers.{root_op}imum_with_index(
                    {accumulator}, {accumulator_index}, {value}, {index_var}
                )
                {accumulator} = {where_cond(f"{accumulator}_next", accumulator)}
                {accumulator_index} = {where_cond(f"{accumulator_index}_next", accumulator_index)}
                """
                )
                final_argreduce(
                    self.post_loop_combine, result_var, accumulator, accumulator_index
                )
            elif is_welford_reduction(reduction_type):
                result_var = self.welford_reduce(
                    result_var, reduction_type, value, where_cond, acc_type, dtype
                )
            elif reduction_type == "online_softmax_reduce":
                accumulator_max = f"_{result_var}_max"
                accumulator_sum = f"_{result_var}_sum"

                # setup accumulator
                self.body.writeline(
                    f"{accumulator_max} = tl.full({self.dense_size_str()}, float('-inf'), {acc_type})"
                )
                self.body.writeline(
                    f"{accumulator_sum} = tl.zeros({self.dense_size_str()}, {acc_type})"
                )

                # combine
                # Note, we pass config.use_fast_math to the JITFunction
                # since a triton kernel can not access a config.
                self.compute.splice(
                    f"""
                    {accumulator_max}_next, {accumulator_sum}_next = triton_helpers.online_softmax_combine(
                        {accumulator_max}, {accumulator_sum}, {value}, {config.use_fast_math}
                    )
                    """
                )

                # mask
                self.compute.splice(
                    f"""
                    {accumulator_max} = {where_cond(f"{accumulator_max}_next", accumulator_max)}
                    {accumulator_sum} = {where_cond(f"{accumulator_sum}_next", accumulator_sum)}
                    """
                )

                # reduce. Similar to the final reduction for coopereative
                # reduction
                result_max = result_var
                result_sum = self.cse.newvar(dtype=dtype, shape=result_max.shape)

                result_var = self.online_softmax_reduce_final_reduction(
                    self.post_loop_combine,
                    result_max,
                    result_sum,
                    accumulator_max,
                    accumulator_sum,
                    dim,
                    dtype,
                )
            else:
                combine_fn = ir.get_reduction_combine_fn(reduction_type, src_dtype)
                updated = combine_fn(accumulator, value)
                if reduction_type == "dot":
                    self.compute.writeline(f"{accumulator} = {updated}")
                else:
                    self.compute.writeline(
                        f"{accumulator} = {where_cond(updated, accumulator)}"
                    )

                if src_dtype == torch.bool:
                    # This is only really used for aten.any. It changes the
                    # final reduction of a non-persistent reduction from
                    #     tmp5 = triton_helpers.max(_tmp5, 1)[:, None]
                    # to
                    #     tmp5 = triton_helpers.max(_tmp5.to(tl.int8), 1)[:, None].to(tl.int1)
                    # which is needed because tl.reduce doesn't support tl.int1
                    accumulator = self.cse.generate(
                        self.post_loop_combine,
                        f"{accumulator}.to(tl.int8)",
                        dtype=torch.int8,
                        shape=accumulator.shape,
                    )

                final_reduction_define(
                    self.post_loop_combine, result_var, accumulator, None
                )

        if self.cooperative_reduction:
            default = ir.Reduction.default_accumulator(reduction_type, src_dtype)
            exit_stack = contextlib.ExitStack()
            for buf in (self.post_loop_combine, self.post_loop_store):
                # only do cooperative reduction combines if we have more than one thread block
                buf.writeline("if HAS_RSPLIT:")
                exit_stack.enter_context(buf.indent())

            if reduction_type in ("argmax", "argmin"):
                self.post_loop_combine.writeline(
                    f"{result_var}_bval = {self.reduction_resize(f'{result_var}_val')}"
                )
                peer_val = self.codegen_cooperative_reduction_peer_combine(
                    f"{result_var}_bval", src_dtype, default
                )
                index_dtype = self.features.select_index_dtype()
                peer_idx = self.codegen_cooperative_reduction_peer_combine(
                    result_var, index_dtype, torch.iinfo(index_dtype).max
                )
                final_argreduce(self.post_loop_store, result_var, peer_val, peer_idx)
            elif is_welford_reduction(reduction_type):
                assert reduction_type == "welford_reduce"
                result_mean, result_m2, result_weight = result_var
                peer_mean = self.codegen_cooperative_reduction_peer_combine(
                    result_mean,
                    upcast_acc_dtype(src_dtype),
                    default[0],  # type: ignore[index]
                )
                peer_m2 = self.codegen_cooperative_reduction_peer_combine(
                    result_m2,
                    upcast_acc_dtype(src_dtype),
                    default[1],  # type: ignore[index]
                )
                peer_weight = self.codegen_cooperative_reduction_peer_combine(
                    result_weight,
                    upcast_acc_dtype(src_dtype),
                    default[2],  # type: ignore[index]
                )
                self.welford_reduce_final_reduction(
                    self.post_loop_store,
                    result_mean,
                    result_m2,
                    result_weight,
                    peer_mean,
                    peer_m2,
                    peer_weight,
                    dim,
                    dtype,
                )
            elif reduction_type == "online_softmax_reduce":
                result_max, result_sum = result_var
                assert isinstance(default, Sequence)
                peer_max = self.codegen_cooperative_reduction_peer_combine(
                    result_max, upcast_acc_dtype(src_dtype), default[0]
                )
                peer_sum = self.codegen_cooperative_reduction_peer_combine(
                    result_sum, upcast_acc_dtype(src_dtype), default[1]
                )
                self.online_softmax_reduce_final_reduction(
                    self.post_loop_store,
                    result_max,
                    result_sum,
                    peer_max,
                    peer_sum,
                    dim,
                    dtype,
                )
            else:
                peers = self.codegen_cooperative_reduction_peer_combine(
                    result_var, upcast_acc_dtype(src_dtype), default
                )
                final_reduction_define(self.post_loop_store, result_var, peers, None)
            exit_stack.close()

        self.cse.reduction_cache[cache_key] = result_var

        result_tuple = result_var if isinstance(result_var, tuple) else (result_var,)
        self.outside_loop_vars.update(result_tuple)
        assert all(isinstance(x, TritonCSEVariable) for x in result_tuple)

        # If BF16/F16 upcasting was done, ensure the output is downcast to the
        # expected dtype.
        if do_upcast:
            for result in result_tuple:
                if result.dtype != original_dtype:
                    self.post_loop_combine.writeline(
                        f"{result} = {result}.to({triton_compute_type(original_dtype)})"
                    )

        return result_var