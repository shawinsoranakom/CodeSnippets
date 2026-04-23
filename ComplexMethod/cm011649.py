def unload_xpu_triton_pyds() -> None:
    # unload __triton_launcher.pyd
    for module_name in list(sys.modules.keys()):
        if not module_name.startswith("torch._inductor.runtime.compile_tasks."):
            continue
        m = sys.modules[module_name]
        for attr_name in m.__dict__:
            if attr_name.startswith("triton_"):
                kernel = getattr(m, attr_name)
                if isinstance(
                    kernel, torch._inductor.runtime.triton_heuristics.CachingAutotuner
                ):
                    for result in kernel.compile_results:
                        if isinstance(
                            result,
                            torch._inductor.runtime.triton_heuristics.TritonCompileResult,
                        ):
                            # pyrefly: ignore [missing-attribute]
                            result.kernel.run.mod.__del__()
        del sys.modules[module_name]

    # unload spirv_utils.pyd
    if "triton.runtime.driver" in sys.modules:
        mod = sys.modules["triton.runtime.driver"]
        del type(mod.driver.active.utils).instance
        del mod.driver.active.utils

    gc.collect()