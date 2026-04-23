def run_cli(args: Sequence[str]) -> None:
    invocation_cmd = args[0]
    args = args[1:]

    # Prepare the argument parser
    parser = argparse.ArgumentParser(
        prog=invocation_cmd,
        description=f"{invocation_cmd} will run the specified AutoGen scenarios for a given number of repetitions and record all logs and trace information. When running in a Docker environment (default), each run will begin from a common, tightly controlled, environment. The resultant logs can then be further processed by other scripts to produce metrics.".strip(),
    )

    parser.add_argument(
        "scenario",
        help="The JSONL scenario file to run. If a directory is specified, then all JSONL scenarios in the directory are run. If set to '-', then read from stdin.",
    )
    parser.add_argument(
        "-r",
        "--repeat",
        type=int,
        help="The number of repetitions to run for each scenario (default: 1).",
        default=1,
    )
    parser.add_argument(
        "-s",
        "--subsample",
        type=str,
        help='Run on a subsample of the tasks in the JSONL file(s). If a decimal value is specified, then run on the given proportion of tasks in each file. For example "0.7" would run on 70%% of tasks, and "1.0" would run on 100%% of tasks. If an integer value is specified, then randomly select *that* number of tasks from each specified JSONL file. For example "7" would run tasks, while "1" would run only 1 task from each specified JSONL file. (default: 1.0; which is 100%%)',
        default=None,
    )
    parser.add_argument(
        "-p",
        "--parallel",
        type=int,
        help="The number of parallel processes to run (default: 1).",
        default=1,
    )
    parser.add_argument(
        "-a",
        "--azure",
        action="store_true",
        help="Use Azure identity to pass an AZURE_OPENAI_AD_TOKEN to the task environment. This is necessary when using Azure-hosted OpenAI models rather than those hosted by OpenAI.",
    )
    parser.add_argument(
        "-e",
        "--env",
        type=str,
        help="The environment file to load into Docker, or into the native task context (default: '"
        + DEFAULT_ENV_FILE_YAML
        + "').",
        default=None,
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="The config file to copy into the Task (default: '" + DEFAULT_CONFIG_YAML + "').",
        default=None,
    )
    parser.add_argument(
        "-d",
        "--docker-image",
        type=str,
        help="The Docker image to use when running scenarios. Can not be used together with --native. (default: '"
        + DEFAULT_DOCKER_IMAGE_TAG
        + "', which will be created if not present)",
        default=None,
    )
    parser.add_argument(
        "--native",
        action="store_true",
        help="Run the scenarios natively rather than in docker. NOTE: This is not advisable, and should be done with great caution.",
    )

    parsed_args = parser.parse_args(args)

    if parsed_args.config is not None:
        # Make sure the config file is readable, so that we fail early
        with open(parsed_args.config, "r"):
            pass

    # don't support parallel and subsample together
    if parsed_args.parallel > 1 and parsed_args.subsample is not None:
        sys.exit("The options --parallel and --subsample can not be used together currently. Exiting.")

    # Don't allow both --docker-image and --native on the same command
    if parsed_args.docker_image is not None and parsed_args.native:
        sys.exit("The options --native and --docker-image can not be used together. Exiting.")

    # Warn if running natively
    if parsed_args.native:
        if IS_WIN32:
            sys.exit("Running scenarios with --native is not supported in Windows. Exiting.")

        sys.stderr.write(
            "WARNING: Running natively, without Docker, not only poses the usual risks of executing arbitrary AI generated code on your machine, it also makes it impossible to ensure that each test starts from a known and consistent set of initial conditions. For example, if the agents spend time debugging and installing Python libraries to solve the task, then those libraries will be available to all other runs. In other words, earlier runs can influence later runs, leading to many confounds in testing.\n\n"
        )

        # Does an environment variable override the prompt?
        allow_native = os.environ.get("AGBENCH_ALLOW_NATIVE")
        if allow_native is None or allow_native == "":
            choice = input(
                'Are you absolutely sure you want to continue with native execution? Type "Yes" exactly, and in full, to proceed: '
            )
            if choice.strip().lower() != "yes":
                sys.exit("Received '" + choice + "'. Exiting.")
        elif allow_native.strip().lower() != "yes":
            sys.exit(f"Exiting because AGBENCH_ALLOW_NATIVE is '{allow_native}'\n")
        else:
            sys.stderr.write(f"Continuing because AGBENCH_ALLOW_NATIVE is '{allow_native}'\n")
            time.sleep(0.75)  # Pause very briefly so the message isn't lost in the noise

    # Parse the subsample
    subsample = None
    if parsed_args.subsample is not None:
        subsample = float(parsed_args.subsample)
        if "." in parsed_args.subsample:  # Intention is to run on a proportion
            if subsample == 1.0:  # Intention is to run 100%, which is the default
                subsample = None  # None means 100% ... which use None to differentiate from the integer 1
            elif subsample < 0 or subsample > 1.0:
                raise (
                    ValueError(
                        "Subsample must either be an integer (specified without a decimal), or a Real number between 0.0 and 1.0"
                    )
                )

    # Get the Azure bearer token generator if a token wasn't provided and there's any evidence of using Azure
    azure_token_provider = None
    if parsed_args.azure:
        azure_token_provider = get_azure_token_provider()

    # Run the scenario
    if parsed_args.parallel > 1:
        run_parallel(parsed_args)
    else:
        run_scenarios(
            scenario=parsed_args.scenario,
            n_repeats=parsed_args.repeat,
            is_native=True if parsed_args.native else False,
            config_file=parsed_args.config,
            token_provider=azure_token_provider,
            docker_image=parsed_args.docker_image,
            subsample=subsample,
            env_file=parsed_args.env,
        )