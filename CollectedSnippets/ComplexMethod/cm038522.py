def __init__(self, so_file: str | None = None):
        if so_file is None:
            so_file = find_loaded_library("libcudart")
            if so_file is None:
                # libcudart is not loaded in the current process, try hip
                so_file = find_loaded_library("libamdhip64")
                # should be safe to assume now that we are using ROCm
                # as the following assertion should error out if the
                # libhiprtc library is also not loaded
                if so_file is None:
                    so_file = envs.VLLM_CUDART_SO_PATH  # fallback to env var
            assert so_file is not None, (
                "libcudart is not loaded in the current process, "
                "try setting VLLM_CUDART_SO_PATH"
            )
        if so_file not in CudaRTLibrary.path_to_library_cache:
            lib = ctypes.CDLL(so_file)
            CudaRTLibrary.path_to_library_cache[so_file] = lib
        self.lib = CudaRTLibrary.path_to_library_cache[so_file]

        if so_file not in CudaRTLibrary.path_to_dict_mapping:
            _funcs = {}
            for func in CudaRTLibrary.exported_functions:
                f = getattr(
                    self.lib,
                    CudaRTLibrary.cuda_to_hip_mapping[func.name]
                    if current_platform.is_rocm()
                    else func.name,
                )
                f.restype = func.restype
                f.argtypes = func.argtypes
                _funcs[func.name] = f
            CudaRTLibrary.path_to_dict_mapping[so_file] = _funcs
        self.funcs = CudaRTLibrary.path_to_dict_mapping[so_file]