def _resolve_arg_value(self, para: dict, kwargs: dict) -> object:
        ref = (para.get("ref") or "").strip()
        if ref and (ref in kwargs or self._canvas.get_variable_value(ref) is not None):
            return self._resolve_variable_value(ref, kwargs)

        if para.get("value") is not None:
            value = para["value"]
            if isinstance(value, str):
                return self._resolve_template_text(value, kwargs)
            return value

        if ref:
            return self._resolve_variable_value(ref, kwargs)

        return ""