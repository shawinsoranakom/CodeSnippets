def benchmark_in_sub_process(
        cls,
        choices: Sequence[ChoiceCaller],
        input_nodes: list[ir.IRNode],
        layout: ir.Layout,
        input_gen_fns: dict[int, Callable[[ir.Buffer], torch.Tensor]] | None,
        hint_override: int | None = None,
    ):
        from . import autotune_process
        from .codegen.cutlass.kernel import CUTLASSTemplateCaller

        # ATen/Extern kernels are safe to benchmark in the current process.
        extern = [c for c in choices if cls._is_extern(c)]
        non_cutlass = [
            c
            for c in choices
            if not cls._is_extern(c) and not isinstance(c, CUTLASSTemplateCaller)
        ]
        cutlass = [c for c in choices if isinstance(c, CUTLASSTemplateCaller)]

        timings = cls.benchmark_in_current_process(
            extern, input_nodes, layout, input_gen_fns, hint_override=hint_override
        )
        # Order Triton before CUTLASS so valid Triton timings are collected
        # before any CUTLASS kernel can crash the subprocess (#171094)
        timings.update(autotune_process.benchmark_in_sub_process(non_cutlass + cutlass))  # type: ignore[arg-type]
        return timings