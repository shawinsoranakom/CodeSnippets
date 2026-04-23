def init_backend_registration() -> None:
    """
    Register the backend for different devices, including the scheduling
    for kernel code generation and the host side wrapper code generation.
    """
    from .cpp import CppScheduling
    from .cpp_wrapper_cpu import CppWrapperCpu
    from .cpp_wrapper_cpu_array_ref import CppWrapperCpuArrayRef
    from .cpp_wrapper_gpu import CppWrapperGpu
    from .cpp_wrapper_mps import CppWrapperMps
    from .cuda_combined_scheduling import CUDACombinedScheduling
    from .halide import HalideScheduling
    from .mps import MetalScheduling
    from .pallas import PallasScheduling
    from .python_wrapper_mtia import PythonWrapperMtia
    from .triton import TritonScheduling
    from .wrapper import PythonWrapperCodegen
    from .wrapper_fxir import WrapperFxCodegen
    from .xpu.xpu_combined_scheduling import XPUCombinedScheduling

    if get_scheduling_for_device("cpu") is None:
        cpu_backends = {
            "cpp": CppScheduling,
            "halide": HalideScheduling,
            "triton": TritonScheduling,
            "pallas": PallasScheduling,
        }
        register_backend_for_device(
            "cpu",
            lambda scheduling: cpu_backends[config.cpu_backend](scheduling),
            PythonWrapperCodegen,
            CppWrapperCpuArrayRef
            if config.aot_inductor.allow_stack_allocation
            else CppWrapperCpu,
            WrapperFxCodegen,
        )

    if get_scheduling_for_device("cuda") is None:
        # CUDACombinedScheduling combines Triton and CUDA C++ scheduling for CUDA devices via delegation
        cuda_backends = {
            "triton": CUDACombinedScheduling,
            "halide": HalideScheduling,
            "pallas": PallasScheduling,
        }
        register_backend_for_device(
            "cuda",
            lambda scheduling: cuda_backends[config.cuda_backend](scheduling),
            PythonWrapperCodegen,
            CppWrapperGpu,
            WrapperFxCodegen,
        )

    if get_scheduling_for_device("tpu") is None:
        register_backend_for_device(
            "tpu",
            PallasScheduling,
            PythonWrapperCodegen,
            # CppWrapperGpu,
            # WrapperFxCodegen,
        )

    if get_scheduling_for_device("xpu") is None:
        register_backend_for_device(
            "xpu",
            XPUCombinedScheduling,
            PythonWrapperCodegen,
            CppWrapperGpu,
            WrapperFxCodegen,
        )

    if get_scheduling_for_device("tpu") is None:
        tpu_backends = {
            "pallas": PallasScheduling,
        }
        register_backend_for_device(
            "tpu",
            lambda scheduling: tpu_backends[config.tpu_backend](scheduling),
            PythonWrapperCodegen,
        )

    if get_scheduling_for_device("mps") is None:
        register_backend_for_device(
            "mps",
            MetalScheduling,
            PythonWrapperCodegen,
            CppWrapperMps,
            WrapperFxCodegen,
        )

    if get_scheduling_for_device("mtia") is None:
        register_backend_for_device(
            "mtia",
            TritonScheduling,
            PythonWrapperMtia,
            CppWrapperGpu,
            WrapperFxCodegen,
        )

    private_backend = torch._C._get_privateuse1_backend_name()
    if (
        private_backend != "privateuseone"
        and get_scheduling_for_device(private_backend) is None
    ):
        from torch.utils.backend_registration import _get_custom_mod_func

        try:
            device_scheduling = _get_custom_mod_func("Scheduling")
            wrapper_codegen = _get_custom_mod_func("PythonWrapperCodegen")
            cpp_wrapper_codegen = _get_custom_mod_func("CppWrapperCodegen")
            fx_wrapper_codegen = _get_custom_mod_func("WrapperFxCodegen")
            if device_scheduling and wrapper_codegen and cpp_wrapper_codegen:
                register_backend_for_device(
                    private_backend,
                    device_scheduling,
                    wrapper_codegen,
                    cpp_wrapper_codegen,
                    fx_wrapper_codegen,
                )
        except RuntimeError:
            pass