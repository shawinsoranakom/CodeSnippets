def expand_scenario(
    scenario_dir: str, scenario: ScenarioInstance, output_dir: str, config_file: Union[str, None]
) -> None:
    """
    Expand a scenario into a folder.
    Despite some awkwardness created by backwards compatibility and notational conveniences, expansion is conceptually simple.
    It is a series of copy commands (similar to `cp -R`), followed by a series of in-place fine and replace operations.
    """

    template = scenario["template"]

    # Either key works for finding the substiturions list. "values" may be deprecated in the future
    substitutions = scenario["substitutions"] if "substitutions" in scenario else scenario["values"]

    # Older versions are only one-level deep. Convert them,
    if len(substitutions) > 0 and isinstance(substitutions[next(iter(substitutions))], str):
        substitutions = {"scenario.py": cast(Dict[str, str], substitutions)}

    copy_operations: List[Tuple[str, str]] = []

    # Handle file (str), folder (str), or mapping (List) templates
    if isinstance(template, str):
        template_path = os.path.join(scenario_dir, template)
        if os.path.isdir(template_path):
            copy_operations.append((template, ""))
        else:
            copy_operations.append((template, "scenario.py"))
    elif isinstance(template, list):
        for elm in template:
            if isinstance(elm, list):
                copy_operations.append((elm[0], elm[1]))
            else:
                copy_operations.append((elm, ""))
    else:
        raise ValueError("expand_scenario expects an str or list for 'template'")

    # The global includes folder is always copied
    shutil.copytree(
        BASE_TEMPLATE_PATH,
        output_dir,
        ignore=shutil.ignore_patterns("*.example"),
        dirs_exist_ok=False,
    )

    # Expand other folders
    for items in copy_operations:
        src_path = pathlib.Path(os.path.join(scenario_dir, items[0])).absolute()
        dest_path = pathlib.Path(os.path.join(output_dir, items[1])).absolute()

        if os.path.isdir(src_path):
            shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
        else:
            if os.path.isdir(dest_path):
                # If the destination is a directory, use the same filename
                shutil.copyfile(src_path, os.path.join(dest_path, os.path.basename(src_path)))
            else:
                # Otherwuse use the filename provided
                shutil.copyfile(src_path, dest_path)

    # Expand templated files
    for templated_file in substitutions.keys():  # Keys are relative file paths
        # Read the templated file into memory
        template_contents: List[str] = list()
        with open(os.path.join(output_dir, templated_file), "rt") as fh:
            for line in fh:
                template_contents.append(line)

        # Rewrite the templated file with substitutions
        values = substitutions[templated_file]
        with open(os.path.join(output_dir, templated_file), "wt") as fh:
            for line in template_contents:
                for k, v in values.items():
                    line = line.replace(k, v)
                fh.write(line)

    # Copy the config
    if config_file is None:
        if os.path.isfile(DEFAULT_CONFIG_YAML):
            config_file = DEFAULT_CONFIG_YAML

    if config_file is not None:
        src_path = pathlib.Path(config_file).absolute()
        dest_path = pathlib.Path(os.path.join(output_dir, "config.yaml")).absolute()
        shutil.copyfile(src_path, dest_path)
    else:
        logging.warning(f"No {DEFAULT_CONFIG_YAML} file found.")