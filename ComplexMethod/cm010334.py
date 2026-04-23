def _get_make_file(package_name: str, model_names: list[str], device_type: str) -> str:
    ib = IndentedBuffer()

    ib.writelines(
        [
            "cmake_minimum_required(VERSION 3.10)",
            "project(TestProject)",
            "",
            "set(CMAKE_CXX_STANDARD 20)",
            "",
        ]
    )

    from torch._inductor.config import test_configs

    if test_configs.use_libtorch:
        ib.writeline("find_package(Torch REQUIRED)")

    if device_type == "cuda":
        if torch.version.hip:
            ib.writeline("find_package(hip REQUIRED)")
        else:
            ib.writeline("find_package(CUDA REQUIRED)")

    ib.newline()
    for model_name in model_names:
        ib.writeline(f"add_subdirectory({package_name}/data/aotinductor/{model_name}/)")

    ib.writeline("\nadd_executable(main main.cpp)")
    if device_type == "cuda":
        if torch.version.hip:
            ib.writeline("target_compile_definitions(main PRIVATE USE_HIP)")
        else:
            ib.writeline("target_compile_definitions(main PRIVATE USE_CUDA)")
    elif device_type == "xpu":
        ib.writeline("target_compile_definitions(main PRIVATE USE_XPU)")

    model_libs = " ".join(model_names)
    ib.writeline(f"target_link_libraries(main PRIVATE torch {model_libs})")

    if device_type == "cuda":
        if torch.version.hip:
            ib.writeline("target_link_libraries(main PRIVATE hip::host)")
        else:
            ib.writeline("target_link_libraries(main PRIVATE cuda ${CUDA_LIBRARIES})")
    elif device_type == "xpu":
        ib.writeline("target_link_libraries(main PRIVATE sycl ze_loader)")
    return ib.getvalue()