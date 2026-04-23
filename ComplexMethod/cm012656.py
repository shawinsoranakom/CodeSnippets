def warn_mix_layout(self, kernel_name):
        """
        Print message if the kernel have mixed layout inputs.
        Only care about 4D tensor for now.
        """
        if (
            len(self.args.input_buffers) == 1
            and len(self.args.output_buffers) == 1
            and len(self.args.inplace_buffers) == 0
        ):
            # even if input buffer and output buffer have different layout,
            # this can be a layout conversion kernel. No need to warn for
            # the mix layouts.
            return

        argdefs, call_args, _signature, _ = self.args.python_argdefs()
        uniform_stride_order = None
        # pyrefly: ignore [bad-assignment]
        for arg_name in call_args:
            buf = V.graph.try_get_buffer(arg_name)
            if not buf:
                continue
            layout = buf.get_layout()
            if len(layout.size) == 4:
                # ignore the tensor if only 1 dimension is non-zero
                if len([x for x in layout.size if x == 1]) == 3:
                    continue
                stride_order = ir.get_stride_order(layout.stride)
                if uniform_stride_order is None:
                    uniform_stride_order = stride_order
                elif uniform_stride_order != stride_order:
                    msg = yellow_text(
                        f"Expected stride order {uniform_stride_order}, but found stride order"
                        + f" {stride_order} for kernel {kernel_name}"
                    )
                    log.warning(msg)

                    stride_order_list = [
                        ir.get_stride_order(
                            V.graph.get_buffer(name).get_layout().stride
                        )
                        if V.graph.try_get_buffer(name)
                        else None
                        for name in call_args
                    ]
                    size_list = [
                        V.graph.get_buffer(name).get_layout().size
                        if V.graph.try_get_buffer(name)
                        else None
                        for name in call_args
                    ]
                    source_list = [
                        "GraphInput"
                        if name in V.graph.graph_inputs
                        else "IntermediateBuffer"
                        if name in V.graph.name_to_buffer
                        else None
                        for name in call_args
                    ]

                    argdef_names = [x.name for x in argdefs]
                    msg = yellow_text(
                        f"  param names {argdef_names}\n  buf names {call_args}\n  strides {stride_order_list}"
                        + f"\n  sizes {size_list}\n  sources {source_list}\n"
                    )
                    log.warning(msg)
                    return
        msg = green_text(
            f"All the inputs for the triton kernel {kernel_name} have uniform layout"
        )
        log.warning(msg)