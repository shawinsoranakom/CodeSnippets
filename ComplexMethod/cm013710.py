def _check_comm_hook(self, hook):
        if not callable(hook):
            self._log_and_throw(TypeError, "Communication hook must be callable.")

        sig = inspect.signature(hook)
        if (
            sig.parameters["bucket"].annotation != inspect._empty
            and sig.parameters["bucket"].annotation != dist.GradBucket
        ):
            self._log_and_throw(
                ValueError,
                "Communication hook: bucket annotation should be dist.GradBucket.",
            )

        if (
            sig.return_annotation != inspect._empty
            and sig.return_annotation != torch.futures.Future[torch.Tensor]
        ):
            self._log_and_throw(
                ValueError,
                "Communication hook: return annotation should be torch.futures.Future[torch.Tensor].",
            )

        if hook.__name__ in ["bf16_compress_hook", "bf16_compress_wrapper_hook"]:
            cuda_supported = (
                torch.version.cuda is not None
            ) or torch.version.hip is not None
            nccl_supported = (
                dist.is_available()
                and dist.is_nccl_available()
                and torch.cuda.nccl.version() >= (2, 10)
            )
            xpu_xccl_supported = (
                dist.is_available()
                and dist.is_xccl_available()
                and torch.xpu.is_available()
            )

            if not ((cuda_supported and nccl_supported) or xpu_xccl_supported):
                self._log_and_throw(
                    TypeError,
                    "BF16 all reduce communication hook required CUDA 11+ and NCCL 2.10+ or XPU and XCCL",
                )