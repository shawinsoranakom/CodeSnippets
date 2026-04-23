def to_serializable(self) -> dict[str, Any]:
        # Due to TensorizerConfig needing to be msgpack-serializable, it needs
        # support for morphing back and forth between itself and its dict
        # representation

        # TensorizerConfig's representation as a dictionary is meant to be
        # linked to TensorizerConfig in such a way that the following is
        # technically initializable:
        # TensorizerConfig(**my_tensorizer_cfg.to_serializable())

        # This means the dict must not retain non-initializable parameters
        # and post-init attribute states

        # Also don't want to retain private and unset parameters, so only retain
        # not None values and public attributes

        raw_tc_dict = asdict(self)
        blacklisted = []

        if "tensorizer_uri" in raw_tc_dict and "tensorizer_dir" in raw_tc_dict:
            blacklisted.append("tensorizer_dir")

        if "tensorizer_dir" in raw_tc_dict and "lora_dir" in raw_tc_dict:
            blacklisted.append("tensorizer_dir")

        tc_dict = {}
        for k, v in raw_tc_dict.items():
            if (
                k not in blacklisted
                and k not in tc_dict
                and not k.startswith("_")
                and v is not None
            ):
                tc_dict[k] = v

        return tc_dict