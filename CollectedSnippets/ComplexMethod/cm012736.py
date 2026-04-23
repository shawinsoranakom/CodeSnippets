def def_kernel(
        self,
        inputs: list[IRNode],
        outputs: list[IRNode],
        names_str: str = "",
        input_reorder: list[int] | None = None,
    ) -> str:
        """
        Hook called from template code to generate function definition and
        needed args.

        Args:
            inputs: List of input IRNodes
            outputs: List of output IRNodes
            names_str: Comma separated list of input + output argument names.
            input_reorder: The actual order of input nodes.
                           e.g. The template might have input argument defined as [X, W, Bias],
                           and the actual input passed into this template could be [Bias, X, W].
                           In this case, the `input_reorder` would be [2, 0, 1].
            additional_size_args: Additional size arguments for epilogue inputs
        """
        # NB: name order matters here, it's used to match up offsets
        names = [x.strip() for x in names_str.strip().split(",")]
        if len(inputs) + len(outputs) != len(names):
            raise RuntimeError(
                f"{len(inputs) + len(outputs)=} != {len(names)=}, {inputs=}, {outputs=}, {names=}"
            )

        if input_reorder is not None:
            assert len(inputs) == len(input_reorder)
        else:
            input_reorder = list(range(len(inputs)))

        for idx in input_reorder:
            name = names[idx]
            node = inputs[idx]
            if node is not None:
                self.named_nodes[name] = node
                self.args.input_buffers[node.get_name()] = name

        for name, node in zip(names[len(inputs) : len(inputs) + len(outputs)], outputs):
            if node is not None:
                # NB: named nodes must be populated in the order of names
                self.named_nodes[name] = node
                self.args.output_buffers[node.get_name()] = name

        arg_defs, *_ = self.args.cpp_argdefs(DTYPE_TO_CUTLASS_TYPE)

        self.init_layout_args()
        free_symbols: OrderedSet[Expr] = OrderedSet()
        for node in self.named_nodes.values():
            free_symbols |= self._collect_unbound_layout_free_symbols(node)
        size_vars = ["M", "N", "K", "B", "lda", "ldb", "ldc", "ldd"]
        size_vars.extend(str(s) for s in free_symbols)
        self.size_args.extend(free_symbols)
        size_args = [f"const int {s}" for s in size_vars]
        offset_args = [f"const int {name}_offset" for name in self.named_nodes]
        runtime_arg_decls = ",".join(
            [f"{arg.ty} {arg.name}" for arg in self.runtime_arg_info]
        )
        if runtime_arg_decls:
            runtime_arg_decls += ", "

        signature = (
            f"int {self.kernel_name}({', '.join(arg_defs + size_args + offset_args)},\
 {runtime_arg_decls}{self._EXTRA_CPP_ARGS})"
        )
        self.signature = signature
        return signature