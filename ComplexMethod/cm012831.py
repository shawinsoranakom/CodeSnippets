def __init__(self, kernel: CompiledKernel) -> None:
        # pyrefly: ignore [missing-attribute]
        self.name = kernel.src.fn.__name__
        # pyrefly: ignore [missing-attribute]
        self.cubin_path = kernel._cubin_path

        # Used by torch.compile to filter constants in older triton versions
        # pyrefly: ignore [missing-attribute]
        self.arg_names = kernel.src.fn.arg_names

        # Const exprs that are declared by the triton kernel directly
        # Used to generate the kernel launcher's def args
        # pyrefly: ignore [missing-attribute]
        self.declared_constexprs = get_constexprs(kernel.src.fn)

        # pyrefly: ignore [missing-attribute]
        self.hash = kernel.hash

        if triton_knobs is None:
            # pyrefly: ignore [missing-attribute]
            launch_enter = kernel.__class__.launch_enter_hook
            # pyrefly: ignore [missing-attribute]
            launch_exit = kernel.__class__.launch_exit_hook
        else:
            launch_enter = triton_knobs.runtime.launch_enter_hook
            launch_exit = triton_knobs.runtime.launch_exit_hook

        def hook_is_empty(hook: Any) -> bool:
            if hook is None:
                return True
            if (
                triton_knobs
                and (HookChain := getattr(triton_knobs, "HookChain", None)) is not None
                and isinstance(hook, HookChain)
            ):
                # Support hooks after https://github.com/triton-lang/triton/pull/7866
                return len(hook.calls) == 0
            return False

        if not hook_is_empty(launch_enter) or not hook_is_empty(launch_exit):
            raise NotImplementedError(
                "We don't support launch enter or launch exit hooks"
            )
        # pyrefly: ignore [missing-attribute]
        self.num_warps = kernel.metadata.num_warps
        self.shared = (
            # pyrefly: ignore [missing-attribute]
            kernel.shared if hasattr(kernel, "shared") else kernel.metadata.shared
        )

        def needs_scratch_arg(scratch_name: str, param_name: str) -> bool:
            # pyrefly: ignore [missing-attribute]
            if hasattr(kernel.metadata, param_name):
                # pyrefly: ignore [missing-attribute]
                if getattr(kernel.metadata, param_name) > 0:
                    raise NotImplementedError(
                        f"{scratch_name} scratch not yet supported"
                    )
                return True
            return False

        # Newer triton versions pass an extra global scratch parameter to the compiled cuda kernel.
        # Inductor never uses this field or enables it, but we still have to pass
        # an extra None into the set of params if its enabled
        self.has_global_scratch = needs_scratch_arg("Global", "global_scratch_size")
        # same situation for profile scratch - triton-lang/triton#7258
        self.has_profile_scratch = needs_scratch_arg("Profile", "profile_scratch_size")

        # pyrefly: ignore [missing-attribute]
        self.arg_tys = self.arg_ty_from_signature(kernel.src)
        self.function: int | None = None  # Loaded by load_kernel(on the parent process)
        num_ctas = 1
        if hasattr(kernel, "num_ctas"):
            num_ctas = kernel.num_ctas
        elif hasattr(kernel, "metadata"):
            num_ctas = kernel.metadata.num_ctas

        if num_ctas != 1:
            raise NotImplementedError(
                "Static cuda launcher only supports num_ctas == 1"
            )