def persistent_load(saved_id):
            if not isinstance(saved_id, tuple):
                raise AssertionError(
                    f"saved_id must be a tuple, got {type(saved_id).__name__}"
                )
            typename = _maybe_decode_ascii(saved_id[0])
            data = saved_id[1:]

            if typename == "storage":
                storage_type, key, location, size = data
                if storage_type is torch.UntypedStorage:
                    dtype = torch.uint8
                else:
                    dtype = storage_type.dtype

                if key not in loaded_storages:
                    load_tensor(
                        dtype,
                        size,
                        key,
                        _maybe_decode_ascii(location),
                        restore_location,
                    )
                storage = loaded_storages[key]
                # TODO: Once we decide to break serialization FC, we can
                # stop wrapping with TypedStorage
                return torch.storage.TypedStorage(
                    wrap_storage=storage._untyped_storage, dtype=dtype, _internal=True
                )
            elif typename == "reduce_package":
                # to fix BC breaking change, objects on this load path
                # will be loaded multiple times erroneously
                if len(data) == 2:
                    func, args = data
                    return func(self, *args)
                reduce_id, func, args = data
                if reduce_id not in loaded_reduces:
                    loaded_reduces[reduce_id] = func(self, *args)
                return loaded_reduces[reduce_id]
            else:
                f"Unknown typename for persistent_load, expected 'storage' or 'reduce_package' but got '{typename}'"