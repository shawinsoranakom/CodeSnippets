def dec_hook(self, t: type, obj: Any) -> Any:
        # Given native types in `obj`, convert to type `t`.
        if isclass(t):
            if issubclass(t, np.ndarray):
                return self._decode_ndarray(obj)
            if issubclass(t, torch.Tensor):
                return self._decode_tensor(obj)
            if t is slice:
                return slice(*obj)
            if issubclass(t, MultiModalKwargsItem):
                return self._decode_mm_item(obj)
            if issubclass(t, MultiModalKwargsItems):
                return self._decode_mm_items(obj)
            if t is UtilityResult:
                return self._decode_utility_result(obj)
        return obj