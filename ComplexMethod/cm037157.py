def enc_hook(self, obj: Any) -> Any:
        if isinstance(obj, torch.Tensor):
            return self._encode_tensor(obj)

        # Fall back to pickle for object or void kind ndarrays.
        if isinstance(obj, np.ndarray) and obj.dtype.kind not in ("O", "V"):
            return self._encode_ndarray(obj)

        if isinstance(obj, slice):
            # We are assuming only int-based values will be used here.
            return tuple(
                int(v) if v is not None else None
                for v in (obj.start, obj.stop, obj.step)
            )

        if isinstance(obj, MultiModalKwargsItem):
            return self._encode_mm_item(obj)

        if isinstance(obj, MultiModalKwargsItems):
            return self._encode_mm_items(obj)

        if isinstance(obj, UtilityResult):
            result = obj.result
            if not envs.VLLM_ALLOW_INSECURE_SERIALIZATION:
                return None, result
            # Since utility results are not strongly typed, we recursively
            # encode type information for nested structures of lists/dicts
            # to help with correct msgspec deserialization.
            return _encode_type_info_recursive(result), result

        if not envs.VLLM_ALLOW_INSECURE_SERIALIZATION:
            raise TypeError(
                f"Object of type {type(obj)} is not serializable"
                "Set VLLM_ALLOW_INSECURE_SERIALIZATION=1 to allow "
                "fallback to pickle-based serialization."
            )

        if isinstance(obj, FunctionType):
            # `pickle` is generally faster than cloudpickle, but can have
            # problems serializing methods.
            return msgpack.Ext(CUSTOM_TYPE_CLOUDPICKLE, cloudpickle.dumps(obj))

        return msgpack.Ext(
            CUSTOM_TYPE_PICKLE, pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
        )