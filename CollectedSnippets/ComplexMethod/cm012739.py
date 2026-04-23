def _add_cutlass_gemm_choices(
        self,
        choices: list[ChoiceCaller],
        layout: ir.Layout,
        input_nodes: list[Buffer],
        alpha: float | int = 1,
        beta: float | int = 0,
        input_reorder: list[int] | None = None,
        **extra_kwargs,
    ) -> None:
        """
        Adds Cutlass GEMM configurations choices to the auto-tuning list.

        This function mutates the passed list of choices by appending the choices for Cutlass GEMM configs to it.

        Args:
            choices (list): The list to which choices are appended.
            layout (ir.Layout): The layout configuration.
            input_nodes (list): The list of input nodes.
            alpha (float,int): Scaling factor, defaults to 1.
            beta (float,int): Offset, defaults to 0.
            input_reorder (list, optional): Order of the inputs, defaults to None.
            **extra_kwargs: Additional keyword arguments.

        """

        ops = self.gen_ops()

        # pre-computation
        layout_repr: str = str(layout)
        input_tensor_meta: TensorMeta | list[TensorMeta] = TensorMeta.from_irnodes(
            self.input_nodes
        )
        # When input_reorder is set (e.g. [2, 0, 1] for addmm), the kernel
        # function signature is reordered (e.g. from [X, W, Bias] to
        # [Bias, X, W]).  input_tensor_meta must follow the same order
        # because subprocess benchmarking creates tensors from this metadata
        # and passes them positionally to the compiled kernel.  Without this
        # reorder the kernel receives mismatched pointers/strides, causing
        # out-of-bounds GPU memory access for large shapes.
        if self.input_reorder is not None and isinstance(input_tensor_meta, list):
            input_tensor_meta = [input_tensor_meta[idx] for idx in self.input_reorder]
        output_tensor_meta: TensorMeta | list[TensorMeta] = TensorMeta.from_irnodes(
            self.output_node
        )

        with dynamo_timed("CUTLASSGemmTemplate.maybe_append_choice"):
            for name, op in ops:
                for (
                    swizzle
                ) in inductor_cutlass_config.cutlass_max_profiling_swizzle_options:
                    description = f"{name} swizzle={swizzle}"
                    self.maybe_append_choice(
                        choices,
                        op=op,
                        name=name,
                        description=description,
                        input_key=self.cache_key,
                        layout_repr=layout_repr,
                        input_tensor_meta=input_tensor_meta,
                        output_tensor_meta=output_tensor_meta,
                        swizzle=swizzle,
                    )

        if len(ops) == 0:
            log.info(
                "No suitable Cutlass GEMM configs found, fallbacks used "
                "( len(ops)=%d, output_layout=%s, input_layouts=%s, input_strides=%s )",
                len(ops),
                layout,
                [node.get_layout() for node in input_nodes],
                [node.get_stride() for node in input_nodes],
            )
        log.debug(
            "Added %d Cutlass gemm configs.",
            len(ops),
        )