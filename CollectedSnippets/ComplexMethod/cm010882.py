def _stabilize_tensor_subclass_metadata(self, obj: Any) -> Any:
        from torch._opaque_base import OpaqueBase

        if isinstance(obj, OpaqueBase):
            return type(obj).__qualname__
        if isinstance(obj, tuple):
            return tuple(self._stabilize_tensor_subclass_metadata(x) for x in obj)
        if isinstance(obj, list):
            return [self._stabilize_tensor_subclass_metadata(x) for x in obj]
        if isinstance(obj, dict):
            return {
                k: self._stabilize_tensor_subclass_metadata(v) for k, v in obj.items()
            }
        return obj