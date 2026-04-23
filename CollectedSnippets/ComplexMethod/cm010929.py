def _accelerator_graph_capture_health_check(self) -> None:
        # Note [torch.compile x capturable]
        # If we are compiling, we try to take the capturable path automatically by
        # setting the flag to True during tracing. Due to this, we skip all the checks
        # normally required for determining whether we can use CUDA/XPU graphs and
        # shunt the responsibility to torch.inductor. This saves time during tracing
        # since the checks are slow without sacrificing UX since inductor will warn
        # later if CUDA/XPU graphs cannot be enabled, e.g.,
        # https://github.com/pytorch/pytorch/blob/d3ba8901d8640eb16f88b2bfef9df7fa383d4b47/torch/_inductor/compile_fx.py#L390.
        # Thus, when compiling, inductor will determine if cudagraphs
        # can be enabled based on whether there is input mutation or CPU tensors.
        if torch.compiler.is_compiling():
            return

        # Determine available accelerator device
        accelerator = torch.accelerator.current_accelerator(check_available=True)

        if accelerator and accelerator.type in {"cuda", "xpu"}:
            capturing = torch.accelerator.current_stream().is_capturing()

            if capturing and not all(
                group["capturable"] for group in self.param_groups
            ):
                raise RuntimeError(
                    f"Attempting {accelerator.type.upper()} graph capture of step() for an instance of "
                    + self.__class__.__name__
                    + " but param_groups' capturable is False."
                )

            if (
                (not getattr(self, "_warned_capturable_if_run_uncaptured", False))
                and all(group["capturable"] for group in self.param_groups)
                and (not capturing)
            ):
                warnings.warn(
                    "This instance was constructed with capturable=True or some of all the param_groups came with capturable=True, "
                    f"but step() is running without {accelerator.type.upper()} graph capture. If you never intend to graph-capture this "
                    "instance, capturable=True can impair performance, and you should set capturable=False.",
                    stacklevel=2,
                )
                self._warned_capturable_if_run_uncaptured = True