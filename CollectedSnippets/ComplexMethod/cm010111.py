def _save(
    obj,
    zip_file,
    pickle_module,
    pickle_protocol,
    _disable_byteorder_record,
):
    serialized_storages: dict[str, torch.storage.UntypedStorage] = {}
    id_map: dict[int, str] = {}

    # Since loading storages that view the same data with different dtypes is
    # not supported, we need to keep track of the dtype associated with each
    # storage data_ptr and throw an error if the dtype is ever different.
    # TODO: This feature could be added in the future
    storage_dtypes: dict[int, torch.dtype] = {}

    def persistent_id(obj):
        # FIXME: the docs say that persistent_id should only return a string
        # but torch store returns tuples. This works only in the binary protocol
        # see
        # https://docs.python.org/2/library/pickle.html#pickling-and-unpickling-external-objects
        # https://github.com/python/cpython/blob/master/Lib/pickle.py#L527-L537
        if isinstance(obj, torch.storage.TypedStorage) or torch.is_storage(obj):
            if isinstance(obj, torch.storage.TypedStorage):
                # TODO: Once we decide to break serialization FC, this case
                # can be deleted
                storage = obj._untyped_storage
                storage_dtype = obj.dtype
                storage_type_str = obj._pickle_storage_type()
                storage_type = getattr(torch, storage_type_str)
                storage_numel = obj._size()

            else:
                storage = obj
                storage_dtype = torch.uint8
                storage_type = normalize_storage_type(type(obj))
                storage_numel = storage.nbytes()

            # If storage is allocated, ensure that any other saved storages
            # pointing to the same data all have the same dtype. If storage is
            # not allocated, don't perform this check
            if str(storage.device) != "meta" and storage.data_ptr() != 0:
                if storage.data_ptr() in storage_dtypes:
                    if storage_dtype != storage_dtypes[storage.data_ptr()]:
                        raise RuntimeError(
                            "Cannot save multiple tensors or storages that "
                            "view the same data as different types"
                        )
                else:
                    storage_dtypes[storage.data_ptr()] = storage_dtype

            storage_key = id_map.setdefault(storage._cdata, str(len(id_map)))
            if hasattr(obj, "_fake_device") and obj._fake_device is not None:
                location = str(obj._fake_device)
            else:
                location = location_tag(storage)
            serialized_storages[storage_key] = storage

            return ("storage", storage_type, storage_key, location, storage_numel)

        return None

    # Write the pickle data for `obj`
    data_buf = io.BytesIO()

    class PyTorchPickler(pickle_module.Pickler):  # type: ignore[name-defined]
        def persistent_id(self, obj):
            return persistent_id(obj)  # noqa: F821

    pickler = PyTorchPickler(data_buf, protocol=pickle_protocol)
    pickler.dump(obj)

    # The class def keeps the persistent_id closure alive, leaking memory.
    del persistent_id

    data_value = data_buf.getvalue()
    zip_file.write_record("data.pkl", data_value, len(data_value))
    # .format_version is used to track
    #     1. version 1 represents the order of storages being changed from
    #        lexicographical based on keys to numerically ordered based on keys
    #     2. version 2 represents including storage_alignment as a record
    #        within the zipfile
    zip_file.write_record(".format_version", "1", len("1"))
    storage_alignment = str(_get_storage_alignment())
    zip_file.write_record(
        ".storage_alignment", storage_alignment, len(storage_alignment)
    )

    # Write byte order marker
    if not _disable_byteorder_record:
        if sys.byteorder not in ["little", "big"]:
            raise ValueError("Unknown endianness type: " + sys.byteorder)

        zip_file.write_record("byteorder", sys.byteorder, len(sys.byteorder))

    # Write each tensor to a file named tensor/the_tensor_key in the zip archive
    for key in serialized_storages:
        name = f"data/{key}"
        storage = serialized_storages[key]
        num_bytes = storage.nbytes()
        global _serialization_tls
        if _serialization_tls.skip_data:
            zip_file.write_record_metadata(name, num_bytes)
        else:
            # given that we copy things around anyway, we might use storage.cpu()
            # this means to that to get tensors serialized, you need to implement
            # .cpu() on the underlying Storage
            if storage.device.type != "cpu":
                from torch.utils.serialization import config

                if (
                    config.save.use_pinned_memory_for_d2h
                    and (
                        acc := torch.accelerator.current_accelerator(
                            check_available=True
                        )
                    )
                    is not None
                    and acc.type == storage.device.type
                ):
                    new_storage = torch.empty(
                        num_bytes, dtype=torch.uint8, device="cpu", pin_memory=True
                    ).untyped_storage()
                    new_storage.copy_(storage)
                    torch.accelerator.current_stream(storage.device.index).synchronize()
                    storage = new_storage
                else:
                    storage = storage.cpu()
            # Now that it is on the CPU we can directly copy it into the zip file
            zip_file.write_record(name, storage, num_bytes)