def __init__(
        self,
        device_type: str,
        dtype: _dtype | None = None,
        enabled: bool = True,
        cache_enabled: bool | None = None,
    ):
        if not isinstance(device_type, str):
            raise ValueError(
                f"Expected `device_type` of type `str`, got: `{type(device_type)}`"
            )
        self.fast_dtype = (
            torch.get_autocast_dtype(device_type) if dtype is None else dtype
        )
        if torch._jit_internal.is_scripting():
            self._enabled = enabled
            self.device = device_type
            if self.fast_dtype is None:
                raise AssertionError("fast_dtype must not be None in scripting mode")
            return
        self.device = device_type
        if not is_autocast_available(self.device):
            raise RuntimeError(
                f"User specified an unsupported autocast device_type '{self.device}'"
            )

        device_supported_dtypes = [torch.bfloat16, torch.float16]

        self.custom_backend_name = torch._C._get_privateuse1_backend_name()
        if self.device == self.custom_backend_name:
            necessary_funcs = [
                "get_amp_supported_dtype",
            ]
            message = f"Tried to use AMP with the `{self.custom_backend_name}` backend, but the backend has not "
            message += "registered a module or  the module miss some necessary funcs. The backend should register "
            message += "a module by `torch._register_device_module`, and the module must have these funcs: \n"
            message += "`get_amp_supported_dtype() -> List[torch.dtype]`. \n"

            if not hasattr(torch, self.custom_backend_name):
                raise AssertionError(message)
            self.custom_device_mod = getattr(torch, self.custom_backend_name)
            for func in necessary_funcs:
                if not hasattr(self.custom_device_mod, func):
                    raise AssertionError(
                        message + f"But the func `{func}` is missing. \n"
                    )
            device_supported_dtypes = self.custom_device_mod.get_amp_supported_dtype()

        self._cache_enabled = (
            torch.is_autocast_cache_enabled()
            if cache_enabled is None
            else cache_enabled
        )

        device_name = (
            self.device
            if self.device == self.custom_backend_name
            else self.device.upper()
        )
        if enabled:
            # Special case for CUDA AMP and bfloat16 support
            if self.device == "cuda":
                if torch.cuda.amp.common.amp_definitely_not_available():
                    warnings.warn(
                        "CUDA is not available or torch_xla is imported. Disabling autocast.",
                        stacklevel=2,
                    )
                    enabled = False
                elif (
                    self.fast_dtype == torch.bfloat16
                    and not torch.cuda.is_bf16_supported()
                ):
                    raise RuntimeError(
                        "Current CUDA Device does not support bfloat16. Please switch dtype to float16."
                    )
            elif self.fast_dtype not in device_supported_dtypes:
                error_message = (
                    f"In {device_name} autocast, but the target dtype is not supported. Disabling autocast.\n"
                    f"{device_name} Autocast only supports dtypes of "
                    + ", ".join(map(str, device_supported_dtypes))
                    + " currently."
                )
                warnings.warn(error_message, stacklevel=2)
                enabled = False
                # Special case for MPS bfloat16 support on macOS < 14
                if (
                    self.device == "mps"
                    and self.fast_dtype == torch.bfloat16
                    and not torch.backends.mps.is_macos_or_newer(14, 0)
                ):
                    error_message = (
                        "In MPS autocast, but the target dtype torch.bfloat16 is not supported "
                        "on macOS versions below 14. Disabling autocast."
                    )
                    warnings.warn(error_message, stacklevel=2)
                    enabled = False
        self._enabled = enabled