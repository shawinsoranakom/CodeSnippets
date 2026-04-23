def build_pytorch(
    version: str | None,
    cmake_python_library: str | None,
    build_python: bool,
    rerun_cmake: bool,
    cmake_only: bool,
    cmake: CMake,
) -> None:
    my_env = _create_build_env()
    if (
        not check_negative_env_flag("USE_DISTRIBUTED")
        and not check_negative_env_flag("USE_CUDA")
        and not check_negative_env_flag("USE_NCCL")
        and not check_env_flag("USE_SYSTEM_NCCL")
    ):
        checkout_nccl()
    build_test = not check_negative_env_flag("BUILD_TEST")
    cmake.generate(
        version, cmake_python_library, build_python, build_test, my_env, rerun_cmake
    )
    if cmake_only:
        return
    build_custom_step = os.getenv("BUILD_CUSTOM_STEP")
    if build_custom_step:
        try:
            output = subprocess.check_output(
                build_custom_step,
                shell=True,
                stderr=subprocess.STDOUT,
                text=True,
            )
            print("Command output:")
            print(output)
        except subprocess.CalledProcessError as e:
            print("Command failed with return code:", e.returncode)
            print("Output (stdout and stderr):")
            print(e.output)
            raise
    cmake.build(my_env)