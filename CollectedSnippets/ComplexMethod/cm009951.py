def _embed_libomp(self) -> None:
        # Copy libiomp5.dylib/libomp.dylib inside the wheel package on MacOS
        build_lib = Path(self.build_lib)
        build_torch_lib_dir = build_lib / "torch" / "lib"
        build_torch_include_dir = build_lib / "torch" / "include"
        libtorch_cpu_path = build_torch_lib_dir / "libtorch_cpu.dylib"
        if not libtorch_cpu_path.exists():
            return
        # Parse libtorch_cpu load commands
        otool_cmds = (
            subprocess.check_output(["otool", "-l", str(libtorch_cpu_path)])
            .decode("utf-8")
            .split("\n")
        )
        rpaths: list[str] = []
        libs: list[str] = []
        for idx, line in enumerate(otool_cmds):
            if line.strip() == "cmd LC_LOAD_DYLIB":
                lib_name = otool_cmds[idx + 2].strip()
                if not lib_name.startswith("name "):
                    raise AssertionError(
                        f"Expected lib_name to start with 'name ', got: {lib_name}"
                    )
                libs.append(lib_name.split(" ", 1)[1].rsplit("(", 1)[0][:-1])

            if line.strip() == "cmd LC_RPATH":
                rpath = otool_cmds[idx + 2].strip()
                if not rpath.startswith("path "):
                    raise AssertionError(
                        f"Expected rpath to start with 'path ', got: {rpath}"
                    )
                rpaths.append(rpath.split(" ", 1)[1].rsplit("(", 1)[0][:-1])

        omplib_path: str = get_cmake_cache_vars()["OpenMP_libomp_LIBRARY"]  # type: ignore[assignment]
        omplib_name: str = get_cmake_cache_vars()["OpenMP_C_LIB_NAMES"]  # type: ignore[assignment]
        omplib_name += ".dylib"
        omplib_rpath_path = os.path.join("@rpath", omplib_name)

        # This logic is fragile and checks only two cases:
        # - libtorch_cpu depends on `@rpath/libomp.dylib`e (happens when built inside miniconda environment)
        # - libtorch_cpu depends on `/abs/path/to/libomp.dylib` (happens when built with libomp from homebrew)
        if not any(c in libs for c in [omplib_path, omplib_rpath_path]):
            return

        # Copy libomp/libiomp5 from rpath locations
        target_lib = build_torch_lib_dir / omplib_name
        libomp_relocated = False
        install_name_tool_args: list[str] = []
        for rpath in rpaths:
            source_lib = os.path.join(rpath, omplib_name)
            if not os.path.exists(source_lib):
                continue
            self.copy_file(source_lib, target_lib)
            # Delete old rpath and add @loader_lib to the rpath
            # This should prevent deallocate from attempting to package another instance
            # of OpenMP library in torch wheel as well as loading two libomp.dylib into
            # the address space, as libraries are cached by their unresolved names
            install_name_tool_args = [
                "-rpath",
                rpath,
                "@loader_path",
            ]
            libomp_relocated = True
            break
        if not libomp_relocated and os.path.exists(omplib_path):
            self.copy_file(omplib_path, target_lib)
            install_name_tool_args = [
                "-change",
                omplib_path,
                omplib_rpath_path,
            ]
            if "@loader_path" not in rpaths:
                install_name_tool_args += [
                    "-add_rpath",
                    "@loader_path",
                ]
            libomp_relocated = True
        if libomp_relocated:
            install_name_tool_args = [
                "install_name_tool",
                *install_name_tool_args,
                str(libtorch_cpu_path),
            ]
            subprocess.check_call(install_name_tool_args)
        # Copy omp.h from OpenMP_C_FLAGS and copy it into include folder
        omp_cflags: str = get_cmake_cache_vars()["OpenMP_C_FLAGS"]  # type: ignore[assignment]
        if not omp_cflags:
            return
        for include_dir in [
            Path(f.removeprefix("-I"))
            for f in omp_cflags.split(" ")
            if f.startswith("-I")
        ]:
            omp_h = include_dir / "omp.h"
            if not omp_h.exists():
                continue
            target_omp_h = build_torch_include_dir / "omp.h"
            self.copy_file(omp_h, target_omp_h)
            break