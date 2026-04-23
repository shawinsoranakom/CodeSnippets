def load(self, name: str, index: sympy.Expr):
        """
        Load from the memory location 'name', offset by some indexing expression 'index'.
        """
        var = self.args.input(name)
        load_counts = self._load_counts
        load_counts[name] += 1
        make_line: Callable[[str], str | DelayReplaceLine] = identity
        indirect_indexing = self.is_indirect_indexing(index)
        original_index = index
        dtype = V.graph.get_dtype(name)
        indexing = self.indexing(
            index,
            block_ptr=True,
            tma_compatibility_checker=self.tma_compatibility_checker_cls(
                self,
                dtype,
                for_store=False,
                force=False,
            ),
        )

        if isinstance(indexing, IndexingOptions) and self._has_stride1_on_rdim(
            indexing.index
        ):
            self.has_load_with_contiguous_rdim = True

        has_rindex = indexing.has_rindex()
        has_tmpmask = indexing.has_tmpmask()

        # Keep the variable in cache if were going to reuse it. Equiv., if any of the following hold
        #  1) We are doing broadcasting
        #  2) It is a non-coalesced load. The intuition is that if it's
        #  non-coalesced, we will likely load each element multiple times in
        #  practice.
        #  3) It will be used later and it won't be CSE'd. Equiv., if all the following hold
        #   3.1) We are in a reduction loop
        #   3.2) Its not its last use
        #   3.3) This load will not be lifted to the body
        #
        is_coalesced = any(
            i == 1 for i in self.get_strides_of_load(original_index).values()
        )
        if self.is_broadcasted(original_index):
            ep = ", eviction_policy='evict_last'"
        elif not is_coalesced:
            ep = ", eviction_policy='evict_last'"
        elif self.inside_reduction and self.range_trees[-1].is_loop:

            def decide_later():
                if load_counts[name] > expected_count and (
                    has_rindex or indirect_indexing
                ):
                    return "evict_last"
                return "evict_first"

            expected_count = load_counts[name]
            ep = ", eviction_policy='<EP>'"
            make_line = functools.partial(DelayReplaceLine, "<EP>", decide_later)
        else:
            ep = ""

        if (has_tmpmask or has_rindex) and indexing.has_mask():
            if self._load_other:
                other = f", other={constant_repr(self._load_other)}"
            else:
                other = ", other=0.0"
        else:
            other = ""

        """Check if the buffer we're about to load, has
        more than one read dependency
        NOTE: enabled with env variable TORCHINDUCTOR_SKIP_L1
        """
        has_read_deps = True
        if config.triton.skip_l1_cache:
            buffer_read_counts = self.features.buffer_read_counts()
            # Graph inputs, primals_*, arg*_* would not be tracked by `buffer_read_counts`
            # and it'd be fair to expect them to be reused.
            if name in buffer_read_counts:
                has_read_deps = buffer_read_counts[name] > 1
        """Skip L1 cache if we're (pretty?) sure the data is used only once
        """
        skip_l1_cache = (
            not self.is_broadcasted(original_index)
            and not self.inside_reduction
            and not has_read_deps
            and is_coalesced  # for indirect loads is_coalesced is False?
        )
        cachemod = ""
        if skip_l1_cache:
            cachemod = ", cache_modifier='.cg'"

        append_broadcast = None
        shape: BlockShapeType = None

        if should_unwrap_unspec_arg(name):
            line = var
            # unwrapped bf16/fp16 0d tensors are passed in as float32 scalars
            # see triton_utils.py:signature_of
            if dtype in (torch.float16, torch.bfloat16):
                if config.triton.codegen_upcast_to_fp32:
                    dtype = torch.float32
                else:
                    line += f".to({triton_type(dtype)})"
            shape = ()

        else:
            if isinstance(indexing, (BlockPtrOptions, TensorDescriptorOptions)):
                block_descriptor, other = self.codegen_block_ptr(
                    name, var, indexing, other
                )
                if isinstance(indexing, BlockPtrOptions):
                    line = f"tl.load({block_descriptor}{other}{ep}{cachemod})"
                else:
                    line = f"{block_descriptor}.load({V.kernel.index_to_str(indexing.offsets)})"
                line = indexing.codegen_broadcast_and_reshape(
                    line,
                    indexing.block_shape,
                    indexing.final_shape,
                    allow_implicit=True,
                    for_store=False,
                )
                shape = indexing.final_shape
            elif is_sympy_integer_like(original_index):
                line = f"tl.load({var} + ({original_index}))"
                append_broadcast = indexing.expand_str
                shape = ()
            else:
                line = f"tl.load({var} + ({indexing.index_str}), {indexing.mask_str}{ep}{other}{cachemod})"

                # The block shape of tl.load depends on the indexing expression.
                # Inferring shape solely from the mask may miss cases where the mask is constant.
                # Inferring from indexing.expand_shape alone may also fail when dense indexing is absent.
                # so, iterate over variables in the indexexpr to accurately infer the block shape.
                if indexing.expand_shape:
                    shape = indexing.expand_shape
                else:
                    shape = TritonSymbols.get_block_shape(indexing.index)

            if (
                dtype in (torch.float16, torch.bfloat16)
                and config.triton.codegen_upcast_to_fp32
            ):
                line += ".to(tl.float32)"
                dtype = torch.float32
            if dtype == torch.bool and torch.version.hip is None:
                # Workaround for https://github.com/triton-lang/triton/issues/2151
                # tl.load returns int8 when loading from pointer to int1
                # NOTE: Currently causes hangs on bool UTs for ROCm
                line += ".to(tl.int1)"
                dtype = torch.bool

        load_buffer = self.get_load_buffer(indexing)
        self._handle_pdl_before_access(load_buffer, name)
        result_var = self.cse.generate(
            load_buffer, make_line(line), dtype=dtype, shape=shape
        )
        self._handle_pdl_after_load(load_buffer, result_var)
        if result_var.use_count > 1:
            load_counts[name] -= 1  # don't double count cache hit
        assert isinstance(result_var, TritonCSEVariable)
        result_var.mask_vars = indexing.mask_vars  # type: ignore[assignment]

        if append_broadcast:
            line = f"tl.broadcast_to({result_var}, {append_broadcast})"
            result_var = self.cse.generate(
                load_buffer, line, dtype=dtype, shape=indexing.expand_shape
            )
            if indexing.mask_vars:
                if dtype.is_floating_point:
                    zero = "0.0"
                elif dtype == torch.bool:
                    zero = "True"
                else:
                    zero = "0"
                other_val = (
                    constant_repr(self._load_other) if self._load_other else zero
                )
                line = f"tl.where({indexing.mask_str}, {result_var}, {other_val})"
                result_var = self.cse.generate(
                    load_buffer, line, dtype=dtype, shape=result_var.shape
                )

        if not self.inside_reduction or (not indexing.has_rmask() and not has_rindex):
            self.outside_loop_vars.add(result_var)

        return result_var