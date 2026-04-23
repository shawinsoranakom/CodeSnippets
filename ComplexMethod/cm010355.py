def _persistent_id(self, obj):
        if torch.is_storage(obj) or isinstance(obj, torch.storage.TypedStorage):
            storage: Storage
            if isinstance(obj, torch.storage.TypedStorage):
                # TODO: Once we decide to break serialization FC, we can
                # remove this case
                untyped_storage = obj._untyped_storage
                storage_type_str = obj.pickle_storage_type()
                storage_type = getattr(torch, storage_type_str)
                storage = cast(Storage, untyped_storage)
                storage_numel = obj.size()

            elif isinstance(obj, torch.UntypedStorage):
                untyped_storage = obj
                storage = cast(Storage, untyped_storage)
                storage_type = normalize_storage_type(type(storage))
                storage_numel = storage.nbytes()
            else:
                raise RuntimeError(f"storage type not recognized: {type(obj)}")

            location = location_tag(storage)

            # serialize storage if not already written
            storage_present = self.storage_context.has_storage(storage)
            storage_id = self.storage_context.get_or_add_storage(storage)
            if not storage_present:
                if storage.device.type != "cpu":
                    storage = storage.cpu()
                num_bytes = storage.nbytes()
                self.zip_file.write_record(
                    f".data/{storage_id}.storage", storage, num_bytes
                )
            return ("storage", storage_type, storage_id, location, storage_numel)

        if hasattr(obj, "__reduce_package__"):
            if _gate_torchscript_serialization and isinstance(
                obj, torch.jit.RecursiveScriptModule
            ):
                raise Exception(  # noqa: TRY002
                    "Serializing ScriptModules directly into a package is a beta feature. "
                    "To use, set global "
                    "`torch.package.package_exporter._gate_torchscript_serialization` to `False`."
                )
            if self.serialized_reduces.get(id(obj)) is None:
                self.serialized_reduces[id(obj)] = (
                    "reduce_package",
                    id(obj),
                    *obj.__reduce_package__(self),
                )

            return self.serialized_reduces[id(obj)]

        return None