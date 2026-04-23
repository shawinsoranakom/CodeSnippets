def __repr__(self) -> str:
        """Pretty print for logging"""
        params: dict[str, T.Any] = {}
        for k, v in self.__dict__.items():
            if k in ("image_shape", "_name"):
                continue
            if k == "identities":
                params[k] = {i: format_array(m) for i, m in v.items()}
                continue
            if k == "aligned":
                lms = v.landmarks
                params["landmarks"] = None if lms is None else format_array(lms)
                continue
            params[k] = format_array(v) if isinstance(v, np.ndarray) else repr(v)
        s_params = ", ".join(f"{k}={v}" for k, v in params.items())
        return f"{self._name}({s_params})"