def codegen_kernel(self, name=None) -> str:
        """
        Convert the TritonKernel from Inductor SIMD IR to triton code, including inductor triton heuristics, imports,
        metadata, and benchmarking infra.
        """

        code = IndentedBuffer()

        size_hints = {}
        for prefix, numel in self.numels.items():
            if prefix_is_reduction(prefix) and not self.inside_reduction:
                continue

            numel_hint = V.graph.sizevars.optimization_hint(numel)
            size_hint = next_power_of_2(int(numel_hint))
            size_hints[prefix] = size_hint

        if name is None:
            code.splice(self.gen_common_triton_imports())
            device_type = V.graph.get_current_device_or_throw().type
            if device_type == "cpu":
                code.splice("triton_helpers.set_driver_to_cpu()")
            else:
                code.splice("triton_helpers.set_driver_to_gpu()")

            if config.benchmark_kernel:
                code.splice(self.imports_for_benchmark_kernel())

        argdefs, _, signature, _ = self.args.python_argdefs()
        # maps actual expression to SizeArg if it is in sizevars replacements
        for i, arg in enumerate(signature):
            if isinstance(arg, SizeArg):
                # mypy is unhappy about the sympy.Expr
                # type for the key of the dict below
                symbol = cast(sympy.Symbol, arg.expr)
                if symbol in V.graph.sizevars.inv_precomputed_replacements:
                    signature[i] = SizeArg(
                        arg.name, V.graph.sizevars.inv_precomputed_replacements[symbol]
                    )

        mutated_args: OrderedSet[str] = OrderedSet()
        for mutation in self.mutations:
            if mutation in self.args.input_buffers:
                mutated_args.add(self.args.input_buffers[mutation])
            if (
                mutation in self.args.inplace_buffers
                and mutation not in V.graph.removed_buffers
                and mutation not in self.removed_buffers
            ):
                mutated_args.add(
                    cast(InplacedBuffer, self.args.inplace_buffers[mutation]).inner_name
                )
            if mutation in self.args.output_buffers:
                mutation_arg = self.args.output_buffers[mutation]
                assert not isinstance(mutation_arg, RemovedArg)
                mutated_args.add(mutation_arg)

        # Note: [Workspace Mutation]
        # workspace arguments are mutated, but are not marked as mutations in self.mutations
        # because their buffers are added during codegen, and aren't tracked during
        # lowering/scheduling. So we add them as mutated_args explicitly below.
        #
        # In the logic below, we only mark the workspaces a mutated if they are marked with
        # zero_fill: that's because, if we don't expect the buffer to be pre-filled with
        # zeros, then, although we still mutate the data, we don't care about those
        # mutations because we don't make any assumptions about the contents of the
        # workspace buffer.  Similarly, ZERO_PER_GRAPH requires the kernel to return
        # the buffer back to its original state.
        for argname, arg in zip(argdefs, signature):
            if (
                isinstance(arg, WorkspaceArg)
                and arg.zero_mode == WorkspaceZeroMode.ZERO_ON_CALL
            ):
                mutated_args.add(argname.name)

        # pyrefly: ignore [bad-assignment]
        mutated_args = sorted(mutated_args)

        for tree in self.active_range_trees():
            sizearg = SizeArg(f"{tree.prefix}numel", tree.numel)
            signature.append(sizearg)
            argdefs.append(ArgName(sizearg.name))
            # constexpr version causes issues, see
            # https://github.com/pytorch/torchdynamo/pull/1362
            # triton_meta["constants"][len(argdefs)] = V.graph.sizevars.size_hint(
            #     tree.numel
            # )
            # argdefs.append(f"{tree.prefix}numel: tl.constexpr")

        def add_constexpr_arg(arg_name):
            # new versions (but not old versions) of Triton need constexprs included in the signature
            if triton_version_uses_attrs_dict():
                signature.append(ConstexprArg(arg_name))
            argdefs.append(ArgName(arg_name, is_constexpr=True))

        for tree in self.range_trees:
            if tree.is_reduction and self.persistent_reduction:
                # Rn_BLOCK for persistent_reduction is defined in codegen_static_numels
                continue
            if tree.tensor_dim is None:
                continue

            add_constexpr_arg(f"{tree.prefix.upper()}BLOCK")

        if self.cooperative_reduction:
            add_constexpr_arg("RSPLIT")

        if self.mix_order_reduction:
            add_constexpr_arg("RSPLIT_SIZE")
            add_constexpr_arg("NUM_STAGES")

        triton_meta_signature = signature_to_meta(
            signature, size_dtype=self.index_dtype, argdefs=argdefs
        )
        triton_meta: dict[str, Any] = {
            "signature": triton_meta_signature,
            "device": DeviceProperties.create(V.graph.get_current_device_or_throw()),
            "constants": {},
            "native_matmul": (
                torch._inductor.config.triton.native_matmul
                and ("tl.dot" in str(self.body) or "tl.dot" in str(self.compute))
            ),
            **self.triton_meta_common(),
        }

        if self.cooperative_reduction:
            # Cooperative reductions rely on multi-block synchronization that
            # requires cooperative-grid launches to avoid hanging.
            triton_meta["launch_cooperative_grid"] = True

        # Skip memory optimization for forward of the training loop where we expect
        # every new node will increase the peak memory and our greedy approach would
        # introduce a lot of unnecessary cpu copies.
        optimize_mem = V.graph.is_inference or V.graph.is_backward

        inductor_meta = {
            "grid_type": self._get_grid_type().__name__,
            # Triton will not accept an OrderedSet for autotune_hints
            "autotune_hints": set(self.autotune_hints),  # noqa: set_linter
            "kernel_name": str(Placeholder.DESCRIPTIVE_NAME),
            "mutated_arg_names": mutated_args,
            "optimize_mem": optimize_mem,
            "no_x_dim": self.no_x_dim,
            "atomic_add_found": self.atomic_add_found,
            "num_load": self.num_load,
            "num_store": self.num_store,
            "num_reduction": self.num_reduction,
            **self.inductor_meta_common(),
        }

        if self.mix_order_reduction:
            inductor_meta["RSPLIT_SIZE"] = self.rsplit_size

        if config.deterministic or config.test_configs.force_filter_reduction_configs:
            inductor_meta["has_loadstore_with_contiguous_rdim"] = (
                self.has_load_with_contiguous_rdim
                or self.has_store_with_contiguous_rdim
            )

        # Bail on 3d tiling, which has more complicated coalesce patterns
        looped_red = V.kernel.features.is_reduction() and not self.persistent_reduction
        tiling_scores = self.tiling_scores
        two_d_red = len(self.tiling) == 2
        if looped_red and two_d_red:
            memory_stats = self.features.memory_stats(self.tiling)
            dim_stats = memory_stats.persistent.memory.dim[0]
            mem_ops_per_thread = dim_stats.count_per_thread

            if (
                tiling_scores is not None
                and "x" in tiling_scores
                and "r0_" in tiling_scores
            ):
                # large rblock inhibits xblock size, dont attempt if there is a decent amount of
                # reads coalesced by xblock
                r_coalesce_ratio = tiling_scores["r0_"] / max(tiling_scores["x"], 1)
                contiguous_red = r_coalesce_ratio >= INNER_REDUCTION_RATIO_THRESHOLD
            else:
                contiguous_red = (
                    self.features.get_reduction_hint(tiling_scores)
                    == ReductionHint.INNER
                )

            looped_mem = memory_stats.looped.memory.bytes
            persistent_mem = memory_stats.persistent.memory.bytes
            # check that we save significant memory by doing persistent
            saved_bytes_ratio = V.graph.sizevars.optimization_hint(looped_mem) / max(
                V.graph.sizevars.optimization_hint(persistent_mem),
                1,
            )

            # TODO - rnumel should be reasonably close to power of 2
            if (
                # significant memory bandwidth savings
                saved_bytes_ratio >= 1.3
                and contiguous_red
                # TODO - need more detailed register analysis
                and V.graph.sizevars.statically_known_leq(
                    self.features.reduction_numel, 32768
                )
                # We will already generate a persistent config in this case
                and V.graph.sizevars.statically_known_gt(
                    self.features.reduction_numel, 2048
                )
                and mem_ops_per_thread <= 10
            ):
                inductor_meta["add_persistent_rblock"] = True

        if self.tiling_scores:
            inductor_meta["tiling_scores"] = self.tiling_scores

        if self.tma_min_block_sizes:
            inductor_meta["tma_min_block_sizes"] = self.tma_min_block_sizes

        if self.cooperative_reduction:
            inductor_meta["persistent_reduction"] = self.persistent_reduction

        num_gb = None
        if config.benchmark_kernel or config.profile_bandwidth:
            num_gb = self.estimate_kernel_num_bytes() / 1e9
            if num_gb is not None:
                inductor_meta["kernel_num_gb"] = num_gb
        if config.benchmark_kernel:
            flops = self.estimate_flops()
            if flops is not None:
                inductor_meta["kernel_flop"] = flops

        # Triton compiler includes equal_to_1 args into constants even
        # when they are not constexpr. otherwise there may be a segfault
        # during launching the Inductor-compiled Triton kernel.
        # https://github.com/pytorch/pytorch/issues/120478#issuecomment-1962822307
        # https://github.com/triton-lang/triton/blob/231efe9ed2d200be0f69a07c298e4342b08efe3d/python/triton/runtime/jit.py#L384
        for arg_num in equal_1_arg_indices(signature):  # type: ignore[index]
            triton_meta["constants"][signature[arg_num].name] = 1  # type: ignore[index,union-attr]

        self.triton_meta = triton_meta
        self.inductor_meta = inductor_meta

        self.codegen_prologue(self.body)
        self.codegen_body()
        self._filter_pdl(self.body)

        # Compute configs after codegen_body() so we know if the kernel
        # uses atomic ops. On HIP, buffer ops don't support atomics, so
        # we must not tag any args with pointer_range_32 in that case.
        # Also disable pointer_range_32 when the config flag is off.
        if torch.version.hip is not None and (
            self.atomic_add_found or not config.triton.emit_pointer_range_32
        ):
            triton_meta["configs"] = [config_of(signature, pointer_range_override=())]
        else:
            triton_meta["configs"] = [config_of(signature)]

        for helper in self.helper_functions:
            code.writeline("")
            code.splice(helper)

        if self.fixed_config:
            heuristics_line = f"""
                @triton_heuristics.{self._get_heuristic()}(
                    config={self.fixed_config.config!r},
                    filename=__file__,
                    triton_meta={triton_meta!r},
                    inductor_meta={inductor_meta!r}
                )
                @triton.jit
            """
        elif self.inside_reduction:
            reduction_hint = self.features.get_reduction_hint(self.tiling_scores)
            heuristics_line = f"""
                @triton_heuristics.{self._get_heuristic()}(
                    size_hints={size_hints!r},
                    reduction_hint={reduction_hint},
                    filename=__file__,
                    triton_meta={triton_meta!r},
                    inductor_meta={inductor_meta!r}
                )
                @triton.jit
            """
        else:
            tile_hint = ""
            if len(size_hints) == 2:
                if (
                    len(non_constexpr_signature(signature)) == 4
                ):  # input, output and 2 args
                    tile_hint = "tile_hint=TileHint.SQUARE,"
                else:
                    tile_hint = "tile_hint=TileHint.DEFAULT,"
            heuristics_line = f"""
                @triton_heuristics.{self._get_heuristic()}(
                    size_hints={size_hints!r}, {tile_hint}
                    filename=__file__,
                    triton_meta={triton_meta!r},
                    inductor_meta={inductor_meta!r},
                    min_elem_per_thread={self.min_elem_per_thread}
                )
                @triton.jit
            """
        code.splice(heuristics_line)
        kernel_name = name or str(Placeholder.KERNEL_NAME)
        code.writeline(
            f"def {kernel_name}({', '.join(x.full_name() for x in argdefs)}):"
        )
        with code.indent():
            if config.triton.proton_profiling:
                code.writeline(f'pl.enter_scope("{kernel_name}")')
            self.codegen_static_numels(code)
            for old, new in self.args.aliases():
                code.writeline(f"{old} = {new}")
            code.splice(self.body)
            if config.triton.proton_profiling:
                code.writeline(f'pl.exit_scope("{kernel_name}")')

        if config.benchmark_kernel:
            code.splice(self.codegen_kernel_benchmark(num_gb))

        return code.getvalue()