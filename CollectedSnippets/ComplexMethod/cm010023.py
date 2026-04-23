def __dlpack__(
        self,
        *,
        stream: Any | None = -1,
        max_version: tuple[int, int] | None = None,
        dl_device: tuple[enum.IntEnum, int] | None = None,
        copy: bool | None = None,
    ):
        """
        Creates a DLpack `capsule https://data-apis.org/array-api/latest/design_topics/data_interchange.html#data-interchange`_
        of the current tensor to be exported to other libraries.

        This function will be called from the `from_dlpack` method
        of the library that will consume the capsule. `from_dlpack` passes the current
        stream to this method as part of the specification.

        Args:
            stream (integer or None): An optional Python integer representing a
                pointer to a CUDA stream. The current stream is synchronized with
                this stream before the capsule is created, and since the capsule
                shares its storage with the tensor this make it safe to access from
                both streams.  If -1 is passed then no synchronization is performed.
                If 1 (on CUDA) or 0 (on ROCM) then the default stream is used for
                synchronization. This API intentionally slightly deviates from the DLPack
                guidance: the default stream is -1 (stream-preserving; no cross-stream sync),
                because many from_dlpack implementations intend stream preservation.
                For non-CUDA devices, -1 is treated the same as None.

            max_version (tuple[int, int] or None): An optional Python tuple with
                2 integers, representing the maximum version the caller supports. If
                None (default), PyTorch will fallback to DLPack 0.8.

            dl_device (tuple[DLDeviceType, int] or None): An optional tuple specifying
                in which device the exported DLPack capsule should be on. If None (default),
                the exported DLPack capsule will be on the same device as ``self``.

            copy (bool or None): An optional boolean indicating whether or not to copy
                ``self``. If None, PyTorch will copy only if necessary.
        """
        if has_torch_function_unary(self):
            args = (self,)
            kwargs = {
                "stream": stream,
                "max_version": max_version,
                "dl_device": dl_device,
                "copy": copy,
            }
            return handle_torch_function(Tensor.__dlpack__, (self,), *args, **kwargs)

        # DLPack capsules can't capture all of PyTorch's semantics,
        # so we prohibit exporting tensors that would lose their properties like
        # requires_grad and having the conjugate bit set.
        if self.requires_grad:
            raise BufferError(
                "Can't export tensors that require gradient, use tensor.detach()"
            )
        if self.is_conj():
            raise BufferError("Can't export tensors with the conjugate bit set")
        if self.layout != torch.strided:
            raise BufferError(
                "Can't export tensors with layout other than torch.strided"
            )

        if (
            self.device.type == "cuda"
            and self.device.index != torch.cuda.current_device()
        ):
            raise BufferError(
                "Can't export tensors on a different CUDA device index. "
                f"Expected: {self.device.index}. "
                f"Current device: {torch.cuda.current_device()}."
            )

        if stream is not None and type(stream) is not int:
            # Stream pointers in CUDA/ROCm are uniquely numbered and can
            # be retrieved from their integer value.
            raise TypeError("stream must be ``int`` or ``none``")
        elif self.device.type == "cuda" and stream != -1:
            # NB: This logic handles the special case values for default
            # streams and must be kept in sync with from_dlpack in
            # torch/utils/dlpack.py
            is_rocm = torch.version.hip is not None
            is_cuda = not is_rocm

            if stream is None or (is_rocm and stream == 0) or (is_cuda and stream == 1):
                stream = torch.cuda.default_stream()
            else:
                if is_cuda and stream == 2:
                    raise BufferError("per-thread default stream is not supported.")

                device_str = "CUDA" if is_cuda else "ROCm"
                if not (
                    (is_cuda and stream != 0) or (is_rocm and stream not in (1, 2))
                ):
                    raise AssertionError(
                        f"unsupported stream on {device_str}: {stream}."
                    )

                stream = torch.cuda.ExternalStream(stream)

            # Only synchronize on different streams
            current_stream = torch.cuda.current_stream()
            if stream != current_stream:
                event = torch.cuda.Event()
                event.record(current_stream)
                stream.wait_event(event)
        elif self.device.type == "cpu":
            if stream is not None and stream != -1:
                raise AssertionError("stream should be None on cpu.")

        if self.device.type == "xla":
            import torch_xla
            import torch_xla.utils.dlpack as xla_dlpack

            if (
                len(torch_xla.real_devices()) <= 0
                or "cuda" not in torch_xla.real_devices()[0].lower()
            ):
                raise RuntimeError(
                    "Can't export to dlpack an XLA tensor that is not on CUDA."
                )

            # Does not support DLPack 1.0, yet.
            return xla_dlpack.to_dlpack(self)

        if max_version is None or max_version[0] < 1:
            # Fallback to the old, unversioned variant.
            return _C._to_dlpack(self, dl_device=dl_device, copy=copy)

        return _C._to_dlpack_versioned(self, dl_device=dl_device, copy=copy)