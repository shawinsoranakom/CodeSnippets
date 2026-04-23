def __init__(self, so_file: str | None = None):
        so_file = so_file or find_nccl_library()

        try:
            if so_file not in NCCLLibrary.path_to_dict_mapping:
                lib = ctypes.CDLL(so_file)
                NCCLLibrary.path_to_library_cache[so_file] = lib
            self.lib = NCCLLibrary.path_to_library_cache[so_file]
        except Exception as e:
            logger.error(
                "Failed to load NCCL library from %s. "
                "It is expected if you are not running on NVIDIA/AMD GPUs."
                "Otherwise, the nccl library might not exist, be corrupted "
                "or it does not support the current platform %s. "
                "If you already have the library, please set the "
                "environment variable VLLM_NCCL_SO_PATH"
                " to point to the correct nccl library path.",
                so_file,
                platform.platform(),
            )
            raise e

        if so_file not in NCCLLibrary.path_to_dict_mapping:
            _funcs: dict[str, Any] = {}
            for func in NCCLLibrary.exported_functions:
                try:
                    f = getattr(self.lib, func.name)
                    f.restype = func.restype
                    f.argtypes = func.argtypes
                    _funcs[func.name] = f
                except AttributeError:
                    if func.name in [
                        "ncclCommWindowRegister",
                        "ncclCommWindowDeregister",
                    ]:
                        if envs.VLLM_USE_NCCL_SYMM_MEM:
                            logger.warning_once(
                                "The symbol %s is not found in the NCCL "
                                "library %s. To enable VLLM_USE_NCCL_SYMM_MEM "
                                " please update your NCCL version to >= "
                                "2.27.03.",
                                func.name,
                                so_file,
                            )
                        if current_platform.is_rocm():
                            # Having an exception here on ROCm platform is
                            # not allowed during graph capturing
                            continue
                    raise
            NCCLLibrary.path_to_dict_mapping[so_file] = _funcs
        self._funcs = NCCLLibrary.path_to_dict_mapping[so_file]