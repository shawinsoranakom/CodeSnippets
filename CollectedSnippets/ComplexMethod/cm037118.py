def __init__(
        self: _T,
        *args,
        vllm_config: VllmConfig | None = None,
        prefix: str = "",
        **kwargs: Any,
    ) -> None:
        if vllm_config is None:
            vllm_config = get_current_vllm_config()

        # NOTE: to support multimodal models (such as encoder),
        # we may not have vllm_config so we may need to patch it
        sig = inspect.signature(old_init)
        # Check that any positional arguments match the old_init method signature
        annotations = [p.annotation for p in sig.parameters.values()]
        for arg, annotation in zip(args, annotations):
            if annotation is inspect._empty:
                continue
            if not isinstance(arg, annotation):
                init = f"'{type(self).__name__}.__init__'"
                arg_type = f"'{type(arg).__name__}'"
                raise TypeError(
                    f"{init} received a positional argument of type {arg_type}, "
                    "but no parameter of that type was found in the method signature. "
                    f"Please either annotate {init} or pass it as a keyword argument."
                )
        if "vllm_config" in sig.parameters:
            kwargs["vllm_config"] = vllm_config
        if "prefix" in sig.parameters:
            kwargs["prefix"] = prefix
        old_init(self, *args, **kwargs)

        self.vllm_config = vllm_config
        self.compilation_config = self.vllm_config.compilation_config
        enable_compile = enable_if is None or enable_if(vllm_config)
        # for CompilationMode.STOCK_TORCH_COMPILE , the upper level model runner
        # will handle the compilation, so we don't need to do anything here.
        self.do_not_compile = (
            self.compilation_config.mode
            in [CompilationMode.NONE, CompilationMode.STOCK_TORCH_COMPILE]
            or _should_ignore_torch_compile(self.__class__)
            or not enable_compile
        )
        if self.do_not_compile:
            return

        self._check_shape_invariants = shape_invariants
        self.was_aot_compile_fn_loaded_from_disk = False
        compilation_counter.num_models_seen += 1
        self.compiled = False

        # Handled by monkeypatching `TorchCompileWithNoGuardsWrapper` into base class
        TorchCompileWithNoGuardsWrapper.__init__(
            self,
            compile_prefix=cls.__name__ if is_encoder else "",
            is_encoder=is_encoder,
        )