def _load(
    zip_file,
    map_location,
    pickle_module,
    pickle_file="data.pkl",
    overall_storage=None,
    **pickle_load_args,
):
    restore_location = _get_restore_location(map_location)

    loaded_storages = {}

    is_meta_map_location = _is_meta_location(map_location)

    can_calculate_storage_offsets = False
    if zip_file.has_record(".format_version"):
        version = zip_file.get_record(".format_version")
        can_calculate_storage_offsets = version >= b"1"

    # check if byteswapping is needed
    byteordername = "byteorder"
    byteorderdata = None
    if zip_file.has_record(byteordername):
        byteorderdata = zip_file.get_record(byteordername)
        if byteorderdata not in [b"little", b"big"]:
            raise ValueError("Unknown endianness type: " + byteorderdata.decode())
    elif (
        get_default_load_endianness() == LoadEndianness.LITTLE
        or get_default_load_endianness() is None
    ):
        byteorderdata = b"little"
    elif get_default_load_endianness() == LoadEndianness.BIG:
        byteorderdata = b"big"
    elif get_default_load_endianness() == LoadEndianness.NATIVE:
        pass
    else:
        raise ValueError("Invalid load endianness type")

    storage_alignment = 64
    if zip_file.has_record(".storage_alignment"):
        storage_alignment = int(zip_file.get_record(".storage_alignment"))

    if (
        not zip_file.has_record(byteordername)
        and get_default_load_endianness() is None
        and sys.byteorder == "big"
    ):
        # Default behaviour was changed
        # See https://github.com/pytorch/pytorch/issues/101688
        warnings.warn(
            "The default load endianness for checkpoints without a byteorder mark "
            "on big endian machines was changed from 'native' to 'little' endian, "
            "to avoid this behavior please use "
            "torch.serialization.set_default_load_endianness to set "
            "the desired default load endianness",
            UserWarning,
            stacklevel=2,
        )

    from torch.utils.serialization import config

    calculate_storage_offsets = config.load.calculate_storage_offsets
    run_debug_asserts = os.environ.get("TORCH_SERIALIZATION_DEBUG", "0") == "1"
    current_offset = None
    # constants from miniz.h/miniz.c
    data_descripter_size64 = 24
    data_descripter_size32 = 16
    mz_uint32_max = 0xFFFFFFFF
    offsets: dict[str, int] = dict()

    def _get_offset(key, name, numel):
        """
        Return the offset of the storage associated with key with record name `name` and size numel.
        It is expected that the zipfile header of this storage starts at current_offset.

        WARNING: This function relies on the behavior of the zipwriter in miniz.c. In particular,
        the behavior of `mz_zip_writer_add_mem_ex_v2`. The behavior of this function must be kept
        in sync with that of miniz!

        After reading a storage of size numel that starts at storage_offset
        if it is the first time that storage was read, update nonlocal variable
        current_offset to the start of the next zipfile header by incrementing
        it by numel and the data descriptor size.
        """
        nonlocal current_offset, offsets
        if name in offsets:
            storage_offset = offsets[name]
            return storage_offset

        if current_offset is None:
            if key != "0":
                raise AssertionError(f"expected key '0', got {key!r}")
            current_offset = zip_file.get_record_offset(name)
            local_header_offset = zip_file.get_record_header_offset(name)
            storage_offset = current_offset
        else:
            storage_offset = zip_file.get_record_offset_no_read(
                current_offset, name, numel, storage_alignment
            )
            local_header_offset = current_offset

        # This is only actually needed for storages that have typed_storage._data_ptr() == 0
        # after being read. Otherwise persistent_load would never "re-call" load_tensor
        # for a given key.
        offsets[name] = storage_offset

        # Increment current_offset to offset where next zipfile header starts
        current_offset = storage_offset + numel
        # add size of data descriptor after payload
        if numel > 0:
            if local_header_offset >= mz_uint32_max or numel >= mz_uint32_max:
                current_offset += data_descripter_size64
            else:
                current_offset += data_descripter_size32

        return storage_offset

    def load_tensor(dtype, nbytes, key, location):
        name = f"data/{key}"
        if torch._guards.detect_fake_mode(None) is not None or is_meta_map_location:
            storage = torch.UntypedStorage(nbytes, device="meta")
            if can_calculate_storage_offsets:
                storage._checkpoint_offset = _get_offset(key, name, nbytes)
            else:
                storage._checkpoint_offset = zip_file.get_record_offset(name)
        elif _serialization_tls.skip_data:
            storage = torch.UntypedStorage(nbytes)
        elif overall_storage is not None:
            if can_calculate_storage_offsets and calculate_storage_offsets:
                storage_offset = _get_offset(key, name, nbytes)
                if run_debug_asserts:
                    if storage_offset != zip_file.get_record_offset(name):
                        raise RuntimeError(
                            "This is a debug assert that was run as the `TORCH_SERIALIZATION_DEBUG` environment "
                            f"variable was set: Incorrect offset for {name}, got {storage_offset} expected "
                            f"{zip_file.get_record_offset(name)}"
                        )
            else:
                storage_offset = zip_file.get_record_offset(name)
            storage = overall_storage[storage_offset : storage_offset + nbytes]
        else:
            if can_calculate_storage_offsets and run_debug_asserts:
                # This is debug code that we use to test the validity of
                # torch.utils.serialization.config.load.calculate_storage_offsets throughout CI
                storage_offset = _get_offset(key, name, nbytes)
                if storage_offset != zip_file.get_record_offset(name):
                    raise RuntimeError(
                        "This is a debug assert that was run as the `TORCH_SERIALIZATION_DEBUG` environment "
                        f"variable was set: Incorrect offset for {name}, got {storage_offset} expected "
                        f"{zip_file.get_record_offset(name)}"
                    )
            storage = (
                zip_file.get_storage_from_record(name, nbytes, torch.UntypedStorage)
                ._typed_storage()
                ._untyped_storage
            )
        # swap here if byteswapping is needed
        if byteorderdata is not None:
            if byteorderdata.decode() != sys.byteorder:
                storage.byteswap(dtype)

        # TODO: Once we decide to break serialization FC, we can
        # stop wrapping with TypedStorage

        if is_meta_map_location:
            # Skip restore_location for meta map_location. Since we already created
            # a meta storage above, calling restore_location would just redundantly
            # call _meta_deserialize which creates another meta storage with the same
            # size.
            wrap_storage = storage
        elif torch._guards.detect_fake_mode(None) is None:
            wrap_storage = restore_location(storage, location)
        else:
            storage._fake_device = location
            wrap_storage = storage

        typed_storage = torch.storage.TypedStorage(
            wrap_storage=wrap_storage,
            dtype=dtype,
            _internal=True,
        )

        if typed_storage._data_ptr() != 0:
            loaded_storages[key] = typed_storage

        return typed_storage

    def persistent_load(saved_id):
        if not isinstance(saved_id, tuple):
            raise AssertionError(
                f"saved_id must be a tuple, got {type(saved_id).__name__}"
            )
        typename = _maybe_decode_ascii(saved_id[0])
        data = saved_id[1:]

        if typename != "storage":
            raise AssertionError(
                f"Unknown typename for persistent_load, expected 'storage' but got '{typename}'"
            )
        storage_type, key, location, numel = data
        if storage_type is torch.UntypedStorage:
            dtype = torch.uint8
        else:
            dtype = storage_type.dtype

        if key in loaded_storages:
            typed_storage = loaded_storages[key]
        else:
            nbytes = numel * torch._utils._element_size(dtype)
            typed_storage = load_tensor(
                dtype, nbytes, key, _maybe_decode_ascii(location)
            )

        return typed_storage

    load_module_mapping: dict[str, str] = {
        # See https://github.com/pytorch/pytorch/pull/51633
        "torch.tensor": "torch._tensor"
    }

    # Need to subclass Unpickler instead of directly monkey-patching the find_class method
    # because it's marked readonly in pickle.
    # The type: ignore is because mypy can't statically determine the type of this class.
    class UnpicklerWrapper(pickle_module.Unpickler):  # type: ignore[name-defined]
        # from https://stackoverflow.com/questions/13398462/unpickling-python-objects-with-a-changed-module-path/13405732
        # Lets us override the imports that pickle uses when unpickling an object.
        # This is useful for maintaining BC if we change a module path that tensor instantiation relies on.
        def find_class(self, mod_name, name):
            if type(name) is str and "Storage" in name:
                try:
                    return StorageType(name)
                except KeyError:
                    pass
            mod_name = load_module_mapping.get(mod_name, mod_name)
            return super().find_class(mod_name, name)

    # Load the data (which may in turn use `persistent_load` to load tensors)
    data_file = io.BytesIO(zip_file.get_record(pickle_file))

    unpickler = UnpicklerWrapper(data_file, **pickle_load_args)
    unpickler.persistent_load = persistent_load
    # Needed for tensors where storage device and rebuild tensor device are
    # not connected (wrapper subclasses and tensors rebuilt using numpy)
    global _serialization_tls
    _serialization_tls.map_location = map_location
    result = unpickler.load()
    _serialization_tls.map_location = None

    torch._utils._validate_loaded_sparse_tensors()
    torch._C._log_api_usage_metadata(
        "torch.load.metadata", {"serialization_id": zip_file.serialization_id()}
    )
    return result