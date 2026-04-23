def get_scenario_env(token_provider: Optional[Callable[[], str]] = None, env_file: str | None = None) -> Dict[str, str]:
    """
    Return a dictionary of environment variables needed to run a scenario.

    Args:
        config_list (list): An AutoGen OAI_CONFIG_LIST to be used when running scenarios.
        env_file (str): The path to the env_file to read. (if None, default to DEFAULT_ENV_FILE)

    Returns: A dictionary of keys and values that need to be added to the system environment.
    """
    env: Dict[str, str] = dict()

    # Populate with commonly needed keys
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if openai_api_key is not None and len(openai_api_key.strip()) > 0:
        env["OPENAI_API_KEY"] = openai_api_key

    ## Support Azure auth tokens
    azure_openai_ad_token = os.environ.get("AZURE_OPENAI_AD_TOKEN")
    if azure_openai_ad_token is None and token_provider is not None:
        azure_openai_ad_token = token_provider()
    if azure_openai_ad_token is not None and len(azure_openai_ad_token.strip()) > 0:
        env["AZURE_OPENAI_AD_TOKEN"] = azure_openai_ad_token

    # Update with any values from the ENV.json file
    env_file_contents: Dict[str, Any] = {}
    if env_file is None:
        # Env file was not specified, so read the default, or warn if the default file is missing.
        if os.path.isfile(DEFAULT_ENV_FILE_YAML):
            with open(DEFAULT_ENV_FILE_YAML, "r") as fh:
                env_file_contents = yaml.safe_load(fh)
        elif os.path.isfile(DEFAULT_ENV_FILE_JSON):
            with open(DEFAULT_ENV_FILE_JSON, "rt") as fh:
                env_file_contents = json.loads(fh.read())
            logging.warning(f"JSON environment files are deprecated. Migrate to '{DEFAULT_ENV_FILE_YAML}'")
        else:
            logging.warning(
                f"The environment file '{DEFAULT_ENV_FILE_YAML}' was not found. A default environment will be provided, containing the keys: {env.keys()}"
            )
    else:
        # Env file was specified. Throw an error if the file can't be read.
        with open(env_file, "rt") as fh:
            if env_file.endswith(".json"):
                logging.warning("JSON environment files are deprecated. Migrate to YAML")
                env_file_contents = json.loads(fh.read())
            else:
                env_file_contents = yaml.safe_load(fh)

    # Apply substitutions in-place
    substitute_env_variables(env_file_contents)

    # Flatten any structures
    for key, value in env_file_contents.items():
        if isinstance(value, dict) or isinstance(value, list):
            env_file_contents[key] = json.dumps(value)

    # Warn about carrying env variables
    if "OPENAI_API_KEY" in env and "OPENAI_API_KEY" not in env_file_contents:
        logging.warning(
            f"Implicit inclusion of OPENAI_API_KEY in the task environment is deprecated. Add it to {DEFAULT_ENV_FILE_YAML} instead. E.g.,\n"
            + """

OPENAI_API_KEY: ${OPENAI_API_KEY}

"""
        )

    # Apply the loaded variables
    env.update(cast(Dict[str, str], env_file_contents))

    return env