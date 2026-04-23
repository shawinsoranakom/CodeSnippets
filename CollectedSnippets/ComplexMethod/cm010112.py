def load(
    f: FileLike,
    map_location: MAP_LOCATION = None,
    pickle_module: Any = None,
    *,
    weights_only: bool | None = None,
    mmap: bool | None = None,
    **pickle_load_args: Any,
) -> Any:
    # Reference: https://github.com/pytorch/pytorch/issues/54354
    # The first line of this docstring overrides the one Sphinx generates for the
    # documentation. We need it so that Sphinx doesn't leak `pickle`s path from
    # the build environment (e.g. `<module 'pickle' from '/leaked/path').

    """load(f, map_location=None, pickle_module=pickle, *, weights_only=True, mmap=None, **pickle_load_args)

    Loads an object saved with :func:`torch.save` from a file.

    .. warning::
        :func:`torch.load()` uses an unpickler under the hood. **Never load data from an untrusted source.**

        See :ref:`weights-only-security` for more details.

    :func:`torch.load` uses Python's unpickling facilities but treats storages,
    which underlie tensors, specially. They are first deserialized on the
    CPU and are then moved to the device they were saved from. If this fails
    (e.g. because the run time system doesn't have certain devices), an exception
    is raised. However, storages can be dynamically remapped to an alternative
    set of devices using the :attr:`map_location` argument.

    If :attr:`map_location` is a callable, it will be called once for each serialized
    storage with two arguments: storage and location. The storage argument
    will be the initial deserialization of the storage, residing on the CPU.
    Each serialized storage has a location tag associated with it which
    identifies the device it was saved from, and this tag is the second
    argument passed to :attr:`map_location`. The builtin location tags are ``'cpu'``
    for CPU tensors and ``'cuda:device_id'`` (e.g. ``'cuda:2'``) for CUDA tensors.
    :attr:`map_location` should return either ``None`` or a storage. If
    :attr:`map_location` returns a storage, it will be used as the final deserialized
    object, already moved to the right device. Otherwise, :func:`torch.load` will
    fall back to the default behavior, as if :attr:`map_location` wasn't specified.

    If :attr:`map_location` is a :class:`torch.device` object or a string containing
    a device tag, it indicates the location where all tensors should be loaded.

    Otherwise, if :attr:`map_location` is a dict, it will be used to remap location tags
    appearing in the file (keys), to ones that specify where to put the
    storages (values).

    User extensions can register their own location tags and tagging and
    deserialization methods using :func:`torch.serialization.register_package`.

    See :ref:`layout-control` for more advanced tools to manipulate a checkpoint.

    Args:
        f: a file-like object (has to implement :meth:`read`, :meth:`readline`, :meth:`tell`, and :meth:`seek`),
            or a string or os.PathLike object containing a file name
        map_location: a function, :class:`torch.device`, string or a dict specifying how to remap storage
            locations
        pickle_module: module used for unpickling metadata and objects (has to
            match the :attr:`pickle_module` used to serialize file)
        weights_only: Indicates whether unpickler should be restricted to
            loading only tensors, primitive types, dictionaries
            and any types added via :func:`torch.serialization.add_safe_globals`.
            See :ref:`weights-only` for more details.
        mmap: Indicates whether the file should be mapped rather than loading all the storages into memory.
            Typically, tensor storages in the file will first be moved from disk to CPU memory, after which they
            are moved to the location that they were tagged with when saving, or specified by ``map_location``. This
            second step is a no-op if the final location is CPU. When the ``mmap`` flag is set, instead of copying the
            tensor storages from disk to CPU memory in the first step, ``f`` is mapped, which means tensor storages
            will be lazily loaded when their data is accessed.
        pickle_load_args: optional keyword arguments passed over to
            :func:`pickle_module.load` and :func:`pickle_module.Unpickler`,
            only works if :attr:`weights_only=False`, e.g., :attr:`errors=...`.

    .. note::
        When you call :func:`torch.load()` on a file which contains GPU tensors, those tensors
        will be loaded to GPU by default. You can call ``torch.load(.., map_location='cpu')``
        and then :meth:`load_state_dict` to avoid GPU RAM surge when loading a model checkpoint.

    .. note::
        By default, we decode byte strings as ``utf-8``.  This is to avoid a common error
        case ``UnicodeDecodeError: 'ascii' codec can't decode byte 0x...``
        when loading files saved by Python 2 in Python 3.  If this default
        is incorrect, you may use an extra :attr:`encoding` keyword argument to specify how
        these objects should be loaded, e.g., :attr:`encoding='latin1'` decodes them
        to strings using ``latin1`` encoding, and :attr:`encoding='bytes'` keeps them
        as byte arrays which can be decoded later with ``byte_array.decode(...)``.

    Example:
        >>> # xdoctest: +SKIP("undefined filepaths")
        >>> torch.load("tensors.pt", weights_only=True)
        # Load all tensors onto the CPU
        >>> torch.load(
        ...     "tensors.pt",
        ...     map_location=torch.device("cpu"),
        ...     weights_only=True,
        ... )
        # Load all tensors onto the CPU, using a function
        >>> torch.load(
        ...     "tensors.pt",
        ...     map_location=lambda storage, loc: storage,
        ...     weights_only=True,
        ... )
        # Load all tensors onto GPU 1
        >>> torch.load(
        ...     "tensors.pt",
        ...     map_location=lambda storage, loc: storage.cuda(1),  # type: ignore[attr-defined]
        ...     weights_only=True,
        ... )  # type: ignore[attr-defined]
        # Map tensors from GPU 1 to GPU 0
        >>> torch.load(
        ...     "tensors.pt",
        ...     map_location={"cuda:1": "cuda:0"},
        ...     weights_only=True,
        ... )
        # Load tensor from io.BytesIO object
        # Loading from a buffer setting weights_only=False, warning this can be unsafe
        >>> with open("tensor.pt", "rb") as f:
        ...     buffer = io.BytesIO(f.read())
        >>> torch.load(buffer, weights_only=False)
        # Load a module with 'ascii' encoding for unpickling
        # Loading from a module setting weights_only=False, warning this can be unsafe
        >>> torch.load("module.pt", encoding="ascii", weights_only=False)
    """
    torch._C._log_api_usage_once("torch.load")
    DOCS_MESSAGE = (
        "\n\nCheck the documentation of torch.load to learn more about types accepted by default with "
        "weights_only https://pytorch.org/docs/stable/generated/torch.load.html."
    )

    def _get_wo_message(message: str) -> str:
        unsafe_global_pattern = r"GLOBAL (\S+) was not an allowed global by default."
        has_unsafe_global = re.search(unsafe_global_pattern, message) is not None
        blocklist_pattern = r"whose module (\S+) is blocked"
        has_blocklist = re.search(blocklist_pattern, message) is not None
        import_pattern = r"(\S+) must be (\S+) to load"
        has_import = re.search(import_pattern, message) is not None
        if has_unsafe_global:
            updated_message = (
                "Weights only load failed. This file can still be loaded, to do so you have two options, "
                "\033[1mdo those steps only if you trust the source of the checkpoint\033[0m. "
                f"\n\t(1) {UNSAFE_MESSAGE}\n\t(2) Alternatively, to load with `weights_only=True` please check "
                "the recommended steps in the following error message.\n\tWeightsUnpickler error: "
                + message
            )
        else:
            if has_import:
                return f"Weights only load failed. {message}\n {UNSAFE_MESSAGE}\n"
            else:
                updated_message = f"Weights only load failed. {UNSAFE_MESSAGE}\n"
                if not has_blocklist:
                    updated_message += (
                        "Please file an issue with the following so that we can make "
                        "`weights_only=True` compatible with your use case: WeightsUnpickler error: "
                    )
            updated_message += "\n\n" + message
        return updated_message + DOCS_MESSAGE

    weights_only_not_set = weights_only is None

    if weights_only_not_set:
        weights_only = _default_to_weights_only(pickle_module)

    true_values = ["1", "y", "yes", "true"]
    # Add ability to force safe only or non-safe weight loads via environment variables
    force_weights_only_load = (
        os.getenv("TORCH_FORCE_WEIGHTS_ONLY_LOAD", "0") in true_values
    )
    force_no_weights_only_load = (
        os.getenv("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "0") in true_values
    )

    if force_weights_only_load and force_no_weights_only_load:
        raise RuntimeError(
            "Only one of `TORCH_FORCE_WEIGHTS_ONLY_LOAD` or `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD` "
            "should be set, but both were set."
        )
    elif force_weights_only_load:
        weights_only = True
    elif force_no_weights_only_load:
        # TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD can only override if callsite did not explicitly set weights_only
        if weights_only_not_set:
            warnings.warn(
                "Environment variable TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD detected, since the"
                "`weights_only` argument was not explicitly passed to `torch.load`, forcing weights_only=False.",
                UserWarning,
                stacklevel=2,
            )
            weights_only = False

    if weights_only:
        if pickle_module is not None:
            raise RuntimeError(
                "Can not safely load weights when explicit pickle_module is specified"
            )
    else:
        if pickle_module is None:
            pickle_module = pickle

    if pickle_load_args != {} and weights_only:
        warnings.warn("pickle_load_args only works if `weights_only=False`.")

    # make flipping default BC-compatible
    if mmap is None:
        from torch.utils.serialization import config

        mmap = config.load.mmap

    _check_dill_version(pickle_module)

    if "encoding" not in pickle_load_args:
        pickle_load_args["encoding"] = "utf-8"

    with _open_file_like(f, "rb") as opened_file:
        if _is_zipfile(opened_file):
            # The zipfile reader is going to advance the current file position.
            # If we want to actually tail call to torch.jit.load, we need to
            # reset back to the original position.
            orig_position = opened_file.tell()
            overall_storage = None
            with _open_zipfile_reader(opened_file) as opened_zipfile:
                if _is_torchscript_zip(opened_zipfile):
                    warnings.warn(
                        "'torch.load' received a zip file that looks like a TorchScript archive"
                        " dispatching to 'torch.jit.load' (call 'torch.jit.load' directly to"
                        " silence this warning)",
                        UserWarning,
                        stacklevel=2,
                    )
                    if weights_only:
                        raise RuntimeError(
                            "Cannot use ``weights_only=True`` with TorchScript archives passed to "
                            "``torch.load``. " + UNSAFE_MESSAGE
                        )
                    opened_file.seek(orig_position)
                    return torch.jit.load(opened_file, map_location=map_location)
                if mmap:
                    if not _is_path(f):
                        raise ValueError(
                            "f must be a file path in order to use the mmap argument"
                        )
                    size = os.path.getsize(f)
                    if not IS_WINDOWS:
                        shared = get_default_mmap_options() == MAP_SHARED
                    else:
                        shared = False
                    overall_storage = torch.UntypedStorage.from_file(
                        os.fspath(f),
                        shared,
                        size,
                    )
                if weights_only:
                    try:
                        return _load(
                            opened_zipfile,
                            map_location,
                            _weights_only_unpickler,
                            overall_storage=overall_storage,
                            **pickle_load_args,
                        )
                    except pickle.UnpicklingError as e:
                        raise pickle.UnpicklingError(_get_wo_message(str(e))) from None
                return _load(
                    opened_zipfile,
                    map_location,
                    pickle_module,
                    overall_storage=overall_storage,
                    **pickle_load_args,
                )
        if mmap:
            f_name = "" if not isinstance(f, str) else f"{f}, "
            raise RuntimeError(
                "mmap can only be used with files saved with "
                f"`torch.save({f_name}_use_new_zipfile_serialization=True), "
                "please torch.save your checkpoint with this option in order to use mmap."
            )
        if weights_only:
            try:
                return _legacy_load(
                    opened_file,
                    map_location,
                    _weights_only_unpickler,
                    **pickle_load_args,
                )
            except pickle.UnpicklingError as e:
                raise pickle.UnpicklingError(_get_wo_message(str(e))) from None
        return _legacy_load(
            opened_file, map_location, pickle_module, **pickle_load_args
        )