def radiance_get_override_params(self, overrides: dict) -> ChromaRadianceParams:
        params = self.params
        if not overrides:
            return params
        params_dict = {k: getattr(params, k) for k in params.__dataclass_fields__}
        nullable_keys = frozenset(("nerf_embedder_dtype",))
        bad_keys = tuple(k for k in overrides if k not in params_dict)
        if bad_keys:
            e = f"Unknown key(s) in transformer_options chroma_radiance_options: {', '.join(bad_keys)}"
            raise ValueError(e)
        bad_keys = tuple(
            k
            for k, v in overrides.items()
            if not isinstance(v, type(getattr(params, k))) and (v is not None or k not in nullable_keys)
        )
        if bad_keys:
            e = f"Invalid value(s) in transformer_options chroma_radiance_options: {', '.join(bad_keys)}"
            raise ValueError(e)
        # At this point it's all valid keys and values so we can merge with the existing params.
        params_dict |= overrides
        return params.__class__(**params_dict)