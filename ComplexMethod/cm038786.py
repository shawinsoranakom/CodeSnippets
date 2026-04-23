def _pull_args_from_config(self, args: list[str]) -> list[str]:
        """Method to pull arguments specified in the config file
        into the command-line args variable.

        The arguments in config file will be inserted between
        the argument list.

        example:
        ```yaml
            port: 12323
            tensor-parallel-size: 4
        ```
        ```python
        $: vllm {serve,chat,complete} "facebook/opt-12B" \
            --config config.yaml -tp 2
        $: args = [
            "serve,chat,complete",
            "facebook/opt-12B",
            '--config', 'config.yaml',
            '-tp', '2'
        ]
        $: args = [
            "serve,chat,complete",
            "facebook/opt-12B",
            '--port', '12323',
            '--tensor-parallel-size', '4',
            '-tp', '2'
            ]
        ```

        Please note how the config args are inserted after the sub command.
        this way the order of priorities is maintained when these are args
        parsed by super().
        """
        assert args.count("--config") <= 1, "More than one config file specified!"

        index = args.index("--config")
        if index == len(args) - 1:
            raise ValueError(
                "No config file specified! Please check your command-line arguments."
            )

        file_path = args[index + 1]

        config_args = self.load_config_file(file_path)

        # 0th index might be the sub command {serve,chat,complete,...}
        # optionally followed by model_tag (only for serve)
        # followed by config args
        # followed by rest of cli args.
        # maintaining this order will enforce the precedence
        # of cli > config > defaults
        if args[0].startswith("-"):
            # No sub command (e.g., api_server entry point)
            args = config_args + args[0:index] + args[index + 2 :]
        elif args[0] == "serve":
            model_in_cli = len(args) > 1 and not args[1].startswith("-")
            model_in_config = any(arg == "--model" for arg in config_args)

            if not model_in_cli and not model_in_config:
                raise ValueError(
                    "No model specified! Please specify model either "
                    "as a positional argument or in a config file."
                )

            if model_in_cli:
                # Model specified as positional arg, keep CLI version
                args = (
                    [args[0]]
                    + [args[1]]
                    + config_args
                    + args[2:index]
                    + args[index + 2 :]
                )
            else:
                # No model in CLI, use config if available
                args = [args[0]] + config_args + args[1:index] + args[index + 2 :]
        else:
            args = [args[0]] + config_args + args[1:index] + args[index + 2 :]

        return args