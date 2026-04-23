def test_cuda_compile_command(self):
        cmd_no_extra_args: str = cuda_compile_command(
            ["abc.cu", "def.cu"], "output", "so"
        )
        if "nvcc " not in cmd_no_extra_args:
            raise AssertionError(cmd_no_extra_args)
        if "abc.cu" not in cmd_no_extra_args:
            raise AssertionError(cmd_no_extra_args)
        if "def.cu" not in cmd_no_extra_args:
            raise AssertionError(cmd_no_extra_args)
        if "output" not in cmd_no_extra_args:
            raise AssertionError(cmd_no_extra_args)
        cmd_extra_args: str = cuda_compile_command(
            ["abc.cu", "def.cu"], "output", "so", ["-Wwhatever", "-nothing"]
        )
        if "nvcc " not in cmd_extra_args:
            raise AssertionError(cmd_extra_args)
        if " -Wwhatever" not in cmd_extra_args:
            raise AssertionError(cmd_extra_args)
        if " -nothing" not in cmd_extra_args:
            raise AssertionError(cmd_extra_args)
        if "abc.cu" not in cmd_extra_args:
            raise AssertionError(cmd_extra_args)
        if "def.cu" not in cmd_extra_args:
            raise AssertionError(cmd_extra_args)
        if "output " not in cmd_extra_args:
            raise AssertionError(cmd_extra_args)
        with mock.patch("subprocess.check_output") as check_output_mock:
            CUDACodeCache.compile("test123.cu", "so", ["-Wsomething"])
            check_output_mock.assert_called()
            cmd_parts: list[str] = check_output_mock.call_args[0][0]
            if not cmd_parts[0].endswith("nvcc"):
                raise AssertionError(cmd_parts)
            if "-Wsomething" not in cmd_parts:
                raise AssertionError(cmd_parts)
            if "-DNDEBUG" not in cmd_parts:
                raise AssertionError(cmd_parts)