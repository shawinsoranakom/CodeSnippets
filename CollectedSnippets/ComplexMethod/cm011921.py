def __init__(
        self,
        choice: ExternKernelChoice,
        input_nodes,
        layout,
        kwargs=None,
        *,
        has_out_variant=True,
    ) -> None:
        super().__init__(choice.name, input_nodes, layout, description="")
        self.choice = choice
        self.kwargs = kwargs or {}
        self.has_out_variant = has_out_variant
        self.gm = choice.gm
        self.bmreq: BenchmarkRequest | None = None

        from torch._inductor.autotune_process import (
            ExternKernelBenchmarkRequest,
            ExternKernelCPUBenchmarkRequest,
            ExternKernelGPUBenchmarkRequest,
        )

        # Determine if this is a GPU or CPU kernel
        if self.layout:
            device = self.layout.device
        else:
            device = None
            for inp_node in self.input_nodes:
                dev = inp_node.get_device()
                if dev and dev.type != "cpu":
                    device = dev
                    break

            if not device:
                device = torch.device("cpu")

        self.input_tensor_meta: list[TensorMeta] | TensorMeta
        self.output_tensor_meta: list[TensorMeta] | TensorMeta
        self.input_tensor_meta, self.output_tensor_meta = [], []
        if device.type == "cpu":
            benchmark_cls = ExternKernelCPUBenchmarkRequest
        else:
            try:
                self.input_tensor_meta = TensorMeta.from_irnodes(self.input_nodes)
                self.output_tensor_meta = TensorMeta.from_irnodes(self.layout)
            except Exception:
                log.warning(
                    "Constructing input/output tensor meta failed for Extern Choice"
                )

            benchmark_cls = ExternKernelGPUBenchmarkRequest

        self.bmreq: ExternKernelBenchmarkRequest = benchmark_cls(
            kernel_name=self.choice.name,
            input_tensor_meta=self.input_tensor_meta,
            output_tensor_meta=self.output_tensor_meta,
            extra_args=(),
            callable_path=self.choice.call_name(),
            kwargs=self.kwargs,
            has_out_variant=self.has_out_variant,
        )