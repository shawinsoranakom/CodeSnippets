def to_dict(self):
        """
        Serializes this instance while replace `Enum` by their values (for JSON serialization support). It obfuscates
        the token values by removing their value.
        """
        # Exclude non-init fields (they aren't user-facing config)
        d = {field.name: getattr(self, field.name) for field in fields(self) if field.init}

        for k, v in d.items():
            if isinstance(v, Enum):
                d[k] = v.value
            if isinstance(v, list) and len(v) > 0 and isinstance(v[0], Enum):
                d[k] = [x.value for x in v]
            if k.endswith("_token"):
                d[k] = f"<{k.upper()}>"
            # Serialize AcceleratorConfig to dict
            if is_accelerate_available() and isinstance(v, AcceleratorConfig):
                d[k] = v.to_dict()
            # Serialize quantization_config if nested inside model_init_kwargs
            if k == "model_init_kwargs" and isinstance(v, dict) and "quantization_config" in v:
                quantization_config = v.get("quantization_config")
                if quantization_config and not isinstance(quantization_config, dict):
                    d[k]["quantization_config"] = quantization_config.to_dict()
            if k == "parallelism_config" and v is not None:
                d[k] = v.to_json()

        self._dict_dtype_to_str(d)

        return d