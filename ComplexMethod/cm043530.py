def to_toml(self, config_file: Path | str, save=True) -> str:
        """Write the configuration to a TOML file."""
        if isinstance(config_file, str):
            config_file = Path(config_file)

        # Load the TOMLDocument and overwrite it with the new values
        config = read_config(config_file)
        default_config = Config().to_dict()
        for k, v in self.to_dict().items():
            # only write values that are already explicitly set, or that differ from defaults
            if k in config or v != default_config[k]:
                if isinstance(v, dict):
                    config[k] = {
                        k2: v2
                        for k2, v2 in v.items()
                        if (
                            k2 in config[k]
                            or default_config.get(k) is None
                            or v2 != default_config[k].get(k2)
                        )
                    }
                else:
                    config[k] = v

        toml_str = tomlkit.dumps(config)
        if save:
            with open(config_file, "w") as f:
                f.write(toml_str)

        return toml_str