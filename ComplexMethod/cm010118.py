def persistent_load(saved_id):
        if not isinstance(saved_id, tuple):
            raise AssertionError(
                f"saved_id must be a tuple, got {type(saved_id).__name__}"
            )
        typename = _maybe_decode_ascii(saved_id[0])
        data = saved_id[1:]

        if typename == "module":
            # Ignore containers that don't have any sources saved
            if all(data[1:]):
                _check_container_source(*data)
            return data[0]
        elif typename == "storage":
            storage_type, root_key, location, numel, view_metadata = data
            location = _maybe_decode_ascii(location)
            dtype = storage_type.dtype

            nbytes = numel * torch._utils._element_size(dtype)

            if root_key not in deserialized_objects:
                if torch._guards.active_fake_mode() is not None:
                    obj = cast(Storage, torch.UntypedStorage(nbytes, device="meta"))
                elif _serialization_tls.skip_data:
                    obj = cast(Storage, torch.UntypedStorage(nbytes))
                    obj = restore_location(obj, location)
                else:
                    obj = cast(Storage, torch.UntypedStorage(nbytes))
                    obj._torch_load_uninitialized = True
                    obj = restore_location(obj, location)
                # TODO: Once we decide to break serialization FC, we can
                # stop wrapping with TypedStorage
                typed_storage = torch.storage.TypedStorage(
                    wrap_storage=obj, dtype=dtype, _internal=True
                )
                deserialized_objects[root_key] = typed_storage
            else:
                typed_storage = deserialized_objects[root_key]
                if typed_storage._data_ptr() == 0:
                    typed_storage = torch.storage.TypedStorage(
                        device=typed_storage._untyped_storage.device,
                        dtype=dtype,
                        _internal=True,
                    )

            if view_metadata is not None:
                view_key, offset, view_size = view_metadata
                offset_bytes = offset * torch._utils._element_size(dtype)
                view_size_bytes = view_size * torch._utils._element_size(dtype)
                if view_key not in deserialized_objects:
                    # TODO: Once we decide to break serialization FC, we can
                    # stop wrapping with TypedStorage
                    deserialized_objects[view_key] = torch.storage.TypedStorage(
                        wrap_storage=typed_storage._untyped_storage[
                            offset_bytes : offset_bytes + view_size_bytes
                        ],
                        dtype=dtype,
                        _internal=True,
                    )
                res = deserialized_objects[view_key]

            else:
                res = typed_storage
            return res
        else:
            raise RuntimeError(f"Unknown saved id type: {saved_id[0]}")