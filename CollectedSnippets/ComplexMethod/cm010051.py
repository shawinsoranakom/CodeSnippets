def __init__(
        self,
        *args,
        device=None,
        dtype=None,
        wrap_storage=None,
        _internal=False,
    ):
        if not _internal:
            _warn_typed_storage_removal()
        arg_error_msg = (
            "TypedStorage.__init__ received an invalid combination "
            "of arguments. Expected one of:\n"
            " * (*, torch.device device, torch.dtype dtype)\n"
            " * (int size, *, torch.device device, torch.dtype dtype)\n"
            " * (Sequence data, *, torch.device device, torch.dtype dtype)\n"
            " * (*, UntypedStorage wrap_storage, torch.dtype dtype)"
        )

        if wrap_storage is not None:
            if len(args) != 0:
                raise RuntimeError(
                    arg_error_msg
                    + "\nNo positional arguments should be given when using "
                    "'wrap_storage'"
                )

            if dtype is None:
                raise RuntimeError(
                    arg_error_msg + "\nArgument 'dtype' must be specified"
                )

            if not isinstance(dtype, torch.dtype):
                raise TypeError(
                    arg_error_msg
                    + f"\nArgument 'dtype' must be torch.dtype, not {type(dtype)}"
                )

            if device is not None:
                raise RuntimeError(
                    arg_error_msg
                    + "\nArgument 'device' should not be specified when 'wrap_storage' is given"
                )

            self.dtype = dtype

            if not isinstance(wrap_storage, torch.UntypedStorage):
                raise TypeError(
                    arg_error_msg
                    + f"\nArgument 'wrap_storage' must be UntypedStorage, but got {type(wrap_storage)}"
                )

            self._untyped_storage = wrap_storage

        else:
            self.dtype = torch.get_default_dtype() if dtype is None else dtype
            device = torch.device("cpu" if device is None else device)

            if self.dtype in [
                torch.quint8,
                torch.quint4x2,
                torch.quint2x4,
                torch.qint32,
                torch.qint8,
            ]:
                if device.type == "cuda":
                    raise RuntimeError(
                        "Cannot create CUDA storage with quantized dtype"
                    )

            if len(args) == 0:
                self._untyped_storage = torch.UntypedStorage(device=device)

            elif len(args) == 1:
                if _isint(args[0]):
                    self._untyped_storage = torch.UntypedStorage(
                        int(args[0]) * self._element_size(), device=device
                    )
                elif isinstance(args[0], collections.abc.Sequence):
                    self._untyped_storage = _get_storage_from_sequence(
                        args[0], self.dtype, device
                    )
                else:
                    raise TypeError(
                        arg_error_msg
                        + f"\nArgument type not recognized: {type(args[0])}"
                    )

            else:
                raise RuntimeError(arg_error_msg + "\nToo many positional arguments")