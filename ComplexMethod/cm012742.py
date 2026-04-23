def filter_op(
        self,
        op: "cutlass_library.gemm_op.GemmOperation",  # type: ignore[name-defined]  # noqa: F821
    ) -> "cutlass_library.gemm_op.GemmOperation":  # type: ignore[name-defined]  # noqa: F821
        """
        Helper method:

        Determines whether a given Cutlass GEMM op definition is suitable for the current
        input / output of the operation that this template is supposed to implement.

        Takes memory layout, dtype and support for EVT operations into account,
        and filters potentially problematic ops.

        Returns None if the op is not suitable, otherwise returns the op to be used, which might
        have been mutated.
        """

        if op.gemm_kind not in self._get_supported_ops():
            return None

        X = self.input_nodes[0]
        W = self.input_nodes[1]

        # Filter ops according to the shape match.
        if not self._shape_match(op):
            return None

        # Filter ops by dtypes.
        if not self._dtype_match(op):
            return None

        # Filter ops by alignment.
        if not self._alignment_match(op):
            log.debug(
                "Skipping due to alignment mismatch. op: %s", op.configuration_name()
            )
            return None

        # only use stream k for static shape
        if op.tile_scheduler.name == "StreamK":
            static_shape = PythonWrapperCodegen.statically_known_list_of_ints_or_none(
                tuple(X.get_size()) + tuple(W.get_size())
            )
            if not static_shape:
                return None

        # Update op.
        op = copy.deepcopy(op)

        # set layouts for X and W
        self.set_layout(op.A, X.get_layout())
        self.set_layout(op.B, W.get_layout())

        # Set output layout.
        op.D.layout = CUTLASSGemmTemplate.cutlass_layout(self.output_node.get_layout())

        # Filter ops by alignments and set alignments.
        status = (
            self.set_alignment(X.get_layout(), op.A)
            and self.set_alignment(W.get_layout(), op.B)
            and self.set_alignment(self.output_node.get_layout(), op.D)
        )
        if not status:
            log.debug(
                "Skipping due to alignment setting failure. op: %s",
                op.configuration_name(),
            )
            return None

        if inductor_cutlass_config.cutlass_tma_only and not self._has_tma_epilogue(op):
            return None

        # Set epilogue.
        # TODO: update epilogue functor according to epilogues.
        op.element_epilogue = op.accumulator_type()

        if (
            self.use_fast_accum is not None
            and int(cutlass_utils._normalize_cuda_arch(cuda_env.get_cuda_arch())) == 90
        ):
            is_op_fast_accum = "fastaccum" in op.configuration_name()
            if self.use_fast_accum ^ is_op_fast_accum:
                return None

        # Set bias layout and alignment.
        status = self._set_bias_layout_and_alignment(op)
        if not status:
            log.debug(
                "Skipping due to bias layout and alignment setting failure. op: %s",
                op.configuration_name(),
            )
            return None

        # Apply regex filters at the end when configuration name doesn't change anymore
        if inductor_cutlass_config.cutlass_op_allowlist_regex:
            if not re.search(
                inductor_cutlass_config.cutlass_op_allowlist_regex,
                op.configuration_name(),
            ):
                return None
        if inductor_cutlass_config.cutlass_op_denylist_regex is not None:
            if re.search(
                inductor_cutlass_config.cutlass_op_denylist_regex,
                op.configuration_name(),
            ):
                return None

        # `_procedural_name` is decorated with @functools.cached_property in cutlass, and its value is
        # cached based on the key `self`. After we modify some attributes of
        # `self` (e.g., layout or alignment), the `self` itself doesn’t change, so the
        # cached value remains stale. We therefore need to clear the cached value so that
        # `_procedural_name` can be recomputed with the updated attributes.
        del op._procedural_name
        return op