def __new__(
        cls,
        *args,
        wrap_storage=None,
        dtype=None,
        device=None,
        _internal=False,
    ):
        if not _internal:
            _warn_typed_storage_removal()

        if cls == torch.storage._LegacyStorage:
            raise RuntimeError(
                "Only child classes of _LegacyStorage can be instantiated"
            )

        if cls == TypedStorage:
            return super().__new__(cls)

        else:
            arg_error_msg = (
                f"{cls}.__new__ received an invalid combination "
                f"of arguments. Expected one of:\n"
                " * no arguments\n"
                " * (int size)\n"
                " * (Sequence data)\n"
                " * (*, UntypedStorage wrap_storage)"
            )

            if device is not None:
                raise RuntimeError(
                    arg_error_msg + "\nKeyword argument 'device' cannot be specified"
                )

            if dtype is not None:
                raise RuntimeError(
                    arg_error_msg + "\nKeyword argument 'dtype' cannot be specified"
                )

            if wrap_storage is None:
                if len(args) > 1:
                    raise RuntimeError(
                        arg_error_msg + "\nToo many positional arguments"
                    )

                if (
                    len(args) == 1
                    and not _isint(args[0])
                    and not isinstance(args[0], collections.abc.Sequence)
                ):
                    raise TypeError(
                        arg_error_msg
                        + f"\nArgument type not recognized: {type(args[0])}"
                    )

                return TypedStorage(
                    *args,
                    dtype=cls._dtype,
                    device=_get_device_from_module(cls.__module__),
                    _internal=True,
                )

            else:
                if len(args) != 0:
                    raise RuntimeError(
                        arg_error_msg
                        + "\nNo positional arguments should be given when using "
                        "'wrap_storage'"
                    )

                if not isinstance(wrap_storage, torch.UntypedStorage):
                    raise TypeError(
                        arg_error_msg
                        + f"\nArgument 'wrap_storage' must be UntypedStorage, but got {type(wrap_storage)}"
                    )

                cls_device = _get_device_from_module(cls.__module__)

                if wrap_storage.device.type != cls_device:
                    raise RuntimeError(
                        arg_error_msg
                        + f"\nDevice of 'wrap_storage' must be {cls_device}"
                        f", but got {wrap_storage.device.type}"
                    )

                return TypedStorage(
                    *args,
                    wrap_storage=wrap_storage,
                    dtype=cls.dtype,
                    _internal=True,
                )