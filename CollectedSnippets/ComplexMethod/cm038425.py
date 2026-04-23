def _create_pynccl() -> EplbCommunicator:
        if tensor_device_type == "cpu":
            raise RuntimeError(
                "EPLB communicator 'pynccl' supports only cuda-like devices "
                f"(got {tensor_device_type})."
            )
        unsupported_dtypes = sorted(
            {
                tensor.dtype
                for tensor in expert_weights
                if not ncclDataTypeEnum.supports_torch_dtype(tensor.dtype)
            },
            key=str,
        )
        if unsupported_dtypes:
            raise RuntimeError(
                "EPLB communicator 'pynccl' requested but expert weights contain "
                "unsupported dtypes: "
                f"({', '.join(str(dtype) for dtype in unsupported_dtypes)})."
            )

        device_comm = group_coordinator.device_communicator
        pynccl_comm = (
            getattr(device_comm, "pynccl_comm", None)
            if device_comm is not None
            else None
        )
        if pynccl_comm is None or pynccl_comm.disabled or not pynccl_comm.available:
            raise RuntimeError("EPLB communicator 'pynccl' requested but unavailable.")
        try:
            return PyNcclEplbCommunicator(pynccl_comm=pynccl_comm)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize PyNcclEplbCommunicator ({exc})."
            ) from exc