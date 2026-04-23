def run(self) -> None:
        # Report build options. This is run after the build completes so # `CMakeCache.txt` exists
        # and we can get an accurate report on what is used and what is not.
        cmake_cache_vars = get_cmake_cache_vars()
        if cmake_cache_vars["USE_NUMPY"]:
            report("-- Building with NumPy bindings")
        else:
            report("-- NumPy not found")
        if cmake_cache_vars["USE_CUDNN"]:
            report(
                "-- Detected cuDNN at "
                f"{cmake_cache_vars['CUDNN_LIBRARY']}, "
                f"{cmake_cache_vars['CUDNN_INCLUDE_DIR']}"
            )
        else:
            report("-- Not using cuDNN")
        if cmake_cache_vars["USE_CUDA"]:
            report(f"-- Detected CUDA at {cmake_cache_vars['CUDA_TOOLKIT_ROOT_DIR']}")
        else:
            report("-- Not using CUDA")
        if cmake_cache_vars["USE_XPU"]:
            report(f"-- Detected XPU runtime at {cmake_cache_vars['SYCL_LIBRARY_DIR']}")
        else:
            report("-- Not using XPU")
        if cmake_cache_vars["USE_MKLDNN"]:
            report("-- Using MKLDNN")
            if cmake_cache_vars["USE_MKLDNN_ACL"]:
                report("-- Using Compute Library for the Arm architecture with MKLDNN")
            else:
                report(
                    "-- Not using Compute Library for the Arm architecture with MKLDNN"
                )
            if cmake_cache_vars["USE_MKLDNN_CBLAS"]:
                report("-- Using CBLAS in MKLDNN")
            else:
                report("-- Not using CBLAS in MKLDNN")
        else:
            report("-- Not using MKLDNN")
        if cmake_cache_vars["USE_NCCL"] and cmake_cache_vars["USE_SYSTEM_NCCL"]:
            report(
                "-- Using system provided NCCL library at "
                f"{cmake_cache_vars['NCCL_LIBRARIES']}, "
                f"{cmake_cache_vars['NCCL_INCLUDE_DIRS']}"
            )
        elif cmake_cache_vars["USE_NCCL"]:
            report("-- Building NCCL library")
        else:
            report("-- Not using NCCL")
        if cmake_cache_vars["USE_DISTRIBUTED"]:
            if IS_WINDOWS:
                report("-- Building without distributed package")
            else:
                report("-- Building with distributed package: ")
                report(f"  -- USE_TENSORPIPE={cmake_cache_vars['USE_TENSORPIPE']}")
                report(f"  -- USE_GLOO={cmake_cache_vars['USE_GLOO']}")
                report(f"  -- USE_MPI={cmake_cache_vars['USE_OPENMPI']}")
        else:
            report("-- Building without distributed package")
        if cmake_cache_vars["STATIC_DISPATCH_BACKEND"]:
            report(
                "-- Using static dispatch with "
                f"backend {cmake_cache_vars['STATIC_DISPATCH_BACKEND']}"
            )
        if cmake_cache_vars["USE_LIGHTWEIGHT_DISPATCH"]:
            report("-- Using lightweight dispatch")

        if cmake_cache_vars["USE_ITT"]:
            report("-- Using ITT")
        else:
            report("-- Not using ITT")

        super().run()

        # Wrap headers with TORCH_STABLE_ONLY and TORCH_TARGET_VERSION guards
        build_lib = Path(self.build_lib)
        build_torch_include_dir = build_lib / "torch" / "include"
        if build_torch_include_dir.exists():
            report(
                "-- Wrapping header files with if !defined(TORCH_STABLE_ONLY) && !defined(TORCH_TARGET_VERSION)"
            )
            self._wrap_headers_with_macro(build_torch_include_dir)

        if IS_DARWIN:
            self._embed_libomp()

        # Copy the essential export library to compile C++ extensions.
        if IS_WINDOWS:
            build_temp = Path(self.build_temp)
            build_lib = Path(self.build_lib)

            ext_filename = self.get_ext_filename("_C")
            lib_filename = ".".join(ext_filename.split(".")[:-1]) + ".lib"

            export_lib = build_temp / "torch" / "csrc" / lib_filename
            target_lib = build_lib / "torch" / "lib" / "_C.lib"

            # Create "torch/lib" directory if not exists.
            # (It is not created yet in "develop" mode.)
            target_dir = target_lib.parent
            target_dir.mkdir(parents=True, exist_ok=True)
            self.copy_file(export_lib, target_lib)