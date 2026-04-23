def normalize(self, metadata):
        if "describe_storage" in metadata:
            storage_meta = metadata["describe_storage"]
            if (storage_id := storage_meta.get("id")) is not None:
                storage_meta["id"] = self._normalize_storage_id(storage_id)
            storage_meta["describer_id"] = "ID"
        if "describe_tensor" in metadata:
            tensor_meta = metadata["describe_tensor"]
            if (tensor_id := tensor_meta.get("id")) is not None:
                tensor_meta["id"] = self._normalize_tensor_id(tensor_id)
            if (storage_id := tensor_meta.get("storage")) is not None:
                tensor_meta["storage"] = self._normalize_storage_id(storage_id)
            tensor_meta["describer_id"] = "ID"
            if "view_func" in tensor_meta:
                tensor_meta["view_func"] = "VIEW_FUNC"
        if "describe_source" in metadata:
            source_meta = metadata["describe_source"]
            if (source_id := source_meta.get("id")) is not None:
                source_meta["id"] = self._normalize_tensor_id(source_id)
            source_meta["describer_id"] = "ID"
        return metadata