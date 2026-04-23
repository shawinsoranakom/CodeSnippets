def __post_init__(self):
        if not config.aot_inductor.link_libtorch:
            return

        if (
            torch._inductor.cpp_builder._IS_MACOS
            or torch._inductor.cpp_builder._IS_WINDOWS
        ):
            return

        if config.aot_inductor.cross_target_platform == "windows":
            return

        if config.aot_inductor.package_cpp_only:
            return

        if not config.enable_autograd_for_aot:
            return

        if isinstance(self.filename, list):
            current_callable = next(
                fn for fn in self.filename if isinstance(fn, str) and fn.endswith(".so")
            )
        else:
            current_callable = self.filename

        if isinstance(current_callable, torch.fx.GraphModule):
            # pyrefly: ignore [bad-assignment]
            self.current_callable = current_callable
            return

        if self.device_type.startswith("cuda"):
            current_callable = (
                torch._C._aoti.AOTIModelContainerRunnerCuda(  # type: ignore[call-arg]
                    current_callable,
                    1,
                    self.device_type,
                    "",
                    True,
                ).run  # type: ignore[attr-defined]
            )  # type: ignore[attr-defined]
        elif self.device_type.startswith("xpu"):
            current_callable = (
                torch._C._aoti.AOTIModelContainerRunnerXpu(  # type: ignore[call-arg]
                    current_callable,
                    1,
                    self.device_type,
                    "",
                ).run  # type: ignore[attr-defined]
            )  # type: ignore[attr-defined]
        elif self.device_type == "cpu":
            current_callable = (
                torch._C._aoti.AOTIModelContainerRunnerCpu(  # type: ignore[call-arg]
                    current_callable, 1
                ).run  # type: ignore[attr-defined]
            )  # type: ignore[attr-defined]
        else:
            raise RuntimeError(f"unsupported device type {self.device_type}")
        self.current_callable = current_callable
        self._boxed_call = True
        for file in self._cached_files:
            if not os.path.exists(file):
                with open(file, "wb") as f:
                    f.write(self._cached_files[file])