def __repr__(self) -> str:
        """Pretty print arrays"""
        params: dict[str, T.Any] = {}
        for k, v in self.__dict__.items():
            if isinstance(v, (list, tuple)) and v and isinstance(v[0], np.ndarray):
                params[k] = [format_array(x) for x in v]
                continue
            if k == "identities" and isinstance(v, dict):
                params[k] = {key: format_array(val) for key, val in v.items()}
                continue
            if isinstance(v, np.ndarray):
                params[k] = format_array(v)
                continue
            params[k] = v

        s_params = ", ".join(f"{k}={v}" for k, v in params.items())
        return f"{self.__class__.__name__}({s_params})"