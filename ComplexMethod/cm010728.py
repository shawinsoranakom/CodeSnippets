def register_autocast(
        self,
        device_type: str,
        cast_inputs: _dtype,
    ):
        r"""Register an autocast dispatch rule for this custom op.

        Valid `device_type` include: "cpu" and "cuda".

        Args:
            op (str | OpOverload): The operator to register an autocast dispatch rule to.
            device_type(str):  Device type to use. 'cuda' or 'cpu'.
                The type is the same as the `type` attribute of a :class:`torch.device`.
                Thus, you may obtain the device type of a tensor using `Tensor.device.type`.
            cast_inputs (:class:`torch.dtype`): When custom op runs in an autocast-enabled region,
                casts incoming floating-point Tensors to the target dtype (non-floating-point Tensors
                are not affected), then executes custom op with autocast disabled.
            lib (Optional[Library]): If provided, the lifetime of this registration

        Examples::
            >>> # xdoctest: +REQUIRES(env:TORCH_DOCTEST_CUDA)
            >>> import torch
            >>> from torch import Tensor
            >>> from torch.library import custom_op
            >>>
            >>> # Create a custom op that works on cuda
            >>> @torch.library.custom_op("mylib::my_sin", mutates_args=())
            >>> def my_sin(x: Tensor) -> Tensor:
            >>>     return torch.sin(x)
            >>>
            >>> # Register autocast dispatch rule for the cuda device
            >>> torch.library.register_autocast("mylib::my_sin", "cuda", torch.float16)
            >>>
            >>> x = torch.randn(3, dtype=torch.float32, device="cuda")
            >>> with torch.autocast("cuda", dtype=torch.float16):
            >>>     y = torch.ops.mylib.my_sin(x)
            >>> assert y.dtype == torch.float16

        """
        if not isinstance(device_type, str):
            raise ValueError(
                f"Expected `device_type` of type `str`, got: `{type(device_type)}`"
            )
        if device_type not in ["cpu", "cuda"]:
            raise ValueError(f"Unknown device type: {device_type}")

        need_register_cuda = self._autocast_cuda_dtype is None
        need_register_cpu = self._autocast_cpu_dtype is None
        if device_type == "cuda":
            self._autocast_cuda_dtype = cast_inputs
        else:
            self._autocast_cpu_dtype = cast_inputs

        def kernel(_, *args, **kwargs):
            if len(kwargs) != 0:
                raise AssertionError(
                    f"Custom ops do not support kwargs yet, got {list(kwargs.keys())}"
                )
            autocast_keyset = torch._C.DispatchKeySet(
                torch._C.DispatchKey.AutocastCPU
            ) | torch._C.DispatchKeySet(torch._C.DispatchKey.AutocastCUDA)
            with torch._C._ExcludeDispatchKeyGuard(autocast_keyset):
                return self._opoverload(*_cast(args, device_type, cast_inputs))

        if need_register_cuda and self._autocast_cuda_dtype:
            self._lib.impl(self._name, kernel, "AutocastCUDA", with_keyset=True)
        elif need_register_cpu and self._autocast_cpu_dtype:
            self._lib.impl(self._name, kernel, "AutocastCPU", with_keyset=True)

        return kernel