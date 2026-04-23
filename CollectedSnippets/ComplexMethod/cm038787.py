def load_config_file(self, file_path: str) -> list[str]:
        """Loads a yaml file and returns the key value pairs as a
        flattened list with argparse like pattern.

        Supports both flat configs and nested YAML structures.

        Flat config example:
        ```yaml
            port: 12323
            tensor-parallel-size: 4
        ```
        returns:
            ['--port', '12323', '--tensor-parallel-size', '4']

        Nested config example:
        ```yaml
            compilation-config:
              pass_config:
                fuse_allreduce_rms: true
            speculative-config:
              model: "nvidia/gpt-oss-120b-Eagle3-v2"
              num_speculative_tokens: 3
        ```
        returns:
            ['--compilation-config', '{"pass_config": {"fuse_allreduce_rms": true}}',
             '--speculative-config', '{"model": "nvidia/gpt-oss-120b-Eagle3-v2", ...}']
        """
        extension: str = file_path.split(".")[-1]
        if extension not in ("yaml", "yml"):
            raise ValueError(
                f"Config file must be of a yaml/yml type. {extension} supplied"
            )

        # Supports both flat configs and nested dicts
        processed_args: list[str] = []

        config: dict[str, Any] = {}
        try:
            with open(file_path) as config_file:
                config = yaml.safe_load(config_file)
        except Exception as ex:
            logger.error(
                "Unable to read the config file at %s. Check path correctness",
                file_path,
            )
            raise ex

        for key, value in config.items():
            if isinstance(value, bool):
                if value:
                    processed_args.append("--" + key)
            elif isinstance(value, list):
                if value:
                    processed_args.append("--" + key)
                    for item in value:
                        processed_args.append(str(item))
            elif isinstance(value, dict):
                # Convert nested dicts to JSON strings so they can be parsed
                # by the existing JSON argument parsing machinery.
                processed_args.append("--" + key)
                processed_args.append(json.dumps(value))
            else:
                processed_args.append("--" + key)
                processed_args.append(str(value))

        return processed_args