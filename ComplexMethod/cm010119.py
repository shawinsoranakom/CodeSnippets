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