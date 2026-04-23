def parse_args(  # type: ignore[override]
        self,
        args: list[str] | None = None,
        namespace: Namespace | None = None,
    ):
        if args is None:
            args = sys.argv[1:]

        if args and args[0] == "serve":
            # Check for --model in command line arguments first
            try:
                model_idx = next(
                    i for i, arg in enumerate(args) if re.match(r"^--model(=.+|$)", arg)
                )
                logger.warning(
                    "With `vllm serve`, you should provide the model as a "
                    "positional argument or in a config file instead of via "
                    "the `--model` option. "
                    "The `--model` option will be removed in a future version."
                )

                if args[model_idx] == "--model":
                    model_tag = args[model_idx + 1]
                    rest_start_idx = model_idx + 2
                else:
                    model_tag = args[model_idx].removeprefix("--model=")
                    rest_start_idx = model_idx + 1

                # Move <model> to the front, e,g:
                # [Before]
                # vllm serve -tp 2 --model <model> --enforce-eager --port 8001
                # [After]
                # vllm serve <model> -tp 2 --enforce-eager --port 8001
                args = [
                    "serve",
                    model_tag,
                    *args[1:model_idx],
                    *args[rest_start_idx:],
                ]
            except StopIteration:
                pass
            # Check for --served-model-name without a positional model argument
            if (
                len(args) > 1
                and args[1].startswith("-")
                and not any(re.match(r"^--config(=.+|$)", arg) for arg in args)
                and any(
                    re.match(r"^--served[-_]model[-_]name(=.+|$)", arg) for arg in args
                )
            ):
                raise ValueError(
                    "`model` should be provided as the first positional argument when "
                    "using `vllm serve`. i.e. `vllm serve <model> --<arg> <value>`."
                )

        if "--config" in args:
            args = self._pull_args_from_config(args)

        def repl(match: re.Match) -> str:
            """Replaces underscores with dashes in the matched string."""
            return match.group(0).replace("_", "-")

        # Everything between the first -- and the first .
        pattern = re.compile(r"(?<=--)[^\.]*")

        # Convert underscores to dashes and vice versa in argument names
        processed_args = list[str]()
        for i, arg in enumerate(args):
            if arg.startswith("--help="):
                FlexibleArgumentParser._search_keyword = arg.split("=", 1)[-1].lower()
                processed_args.append("--help")
            elif arg.startswith("--"):
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    key = pattern.sub(repl, key, count=1)
                    processed_args.append(f"{key}={value}")
                else:
                    key = pattern.sub(repl, arg, count=1)
                    processed_args.append(key)
            elif arg.startswith("-O") and arg != "-O":
                # allow -O flag to be used without space, e.g. -O3 or -Odecode
                # also handle -O=<optimization_level> here
                optimization_level = arg[3:] if arg[2] == "=" else arg[2:]
                processed_args += ["--optimization-level", optimization_level]
            elif (
                arg == "-O"
                and i + 1 < len(args)
                and args[i + 1] in {"0", "1", "2", "3"}
            ):
                # Convert -O <n> to --optimization-level <n>
                processed_args.append("--optimization-level")
            else:
                processed_args.append(arg)

        def create_nested_dict(keys: list[str], value: str) -> dict[str, Any]:
            """Creates a nested dictionary from a list of keys and a value.

            For example, `keys = ["a", "b", "c"]` and `value = 1` will create:
            `{"a": {"b": {"c": 1}}}`
            """
            nested_dict: Any = value
            for key in reversed(keys):
                nested_dict = {key: nested_dict}
            return nested_dict

        def recursive_dict_update(
            original: dict[str, Any],
            update: dict[str, Any],
        ) -> set[str]:
            """Recursively updates a dictionary with another dictionary.
            Returns a set of duplicate keys that were overwritten.
            """
            duplicates = set[str]()
            for k, v in update.items():
                if isinstance(v, dict) and isinstance(original.get(k), dict):
                    nested_duplicates = recursive_dict_update(original[k], v)
                    duplicates |= {f"{k}.{d}" for d in nested_duplicates}
                elif isinstance(v, list) and isinstance(original.get(k), list):
                    original[k] += v
                else:
                    if k in original:
                        duplicates.add(k)
                    original[k] = v
            return duplicates

        delete = set[int]()
        dict_args = defaultdict[str, dict[str, Any]](dict)
        duplicates = set[str]()
        # Track regular arguments (non-dict args) for duplicate detection
        regular_args_seen = set[str]()
        for i, processed_arg in enumerate(processed_args):
            if i in delete:  # skip if value from previous arg
                continue

            if processed_arg.startswith("--") and "." not in processed_arg:
                if "=" in processed_arg:
                    arg_name = processed_arg.split("=", 1)[0]
                else:
                    arg_name = processed_arg

                if arg_name in regular_args_seen:
                    duplicates.add(arg_name)
                else:
                    regular_args_seen.add(arg_name)
                continue

            if processed_arg.startswith("-") and "." in processed_arg:
                if "=" in processed_arg:
                    processed_arg, value_str = processed_arg.split("=", 1)
                    if "." not in processed_arg:
                        # False positive, '.' was only in the value
                        continue
                else:
                    value_str = processed_args[i + 1]
                    delete.add(i + 1)

                if processed_arg.endswith("+"):
                    processed_arg = processed_arg[:-1]
                    value_str = json.dumps(list(value_str.split(",")))

                key, *keys = processed_arg.split(".")
                try:
                    value = json.loads(value_str)
                except json.decoder.JSONDecodeError:
                    value = value_str

                # Merge all values with the same key into a single dict
                arg_dict = create_nested_dict(keys, value)
                arg_duplicates = recursive_dict_update(dict_args[key], arg_dict)
                duplicates |= {f"{key}.{d}" for d in arg_duplicates}
                delete.add(i)
        # Filter out the dict args we set to None
        processed_args = [a for i, a in enumerate(processed_args) if i not in delete]
        if duplicates:
            logger.warning("Found duplicate keys %s", ", ".join(duplicates))

        # Add the dict args back as if they were originally passed as JSON
        for dict_arg, dict_value in dict_args.items():
            processed_args.append(dict_arg)
            processed_args.append(json.dumps(dict_value))

        return super().parse_args(processed_args, namespace)