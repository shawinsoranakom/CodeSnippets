def run_scenarios(
    scenario: str,
    n_repeats: int,
    is_native: bool,
    config_file: Union[None, str],
    token_provider: Optional[Callable[[], str]],
    docker_image: Optional[str] = None,
    results_dir: str = "Results",
    subsample: Union[None, int, float] = None,
    env_file: Union[None, str] = None,
) -> None:
    """
    Run a set agbench scenarios a given number of times.

    Args:
        scenario (path):    The file or folder containing the scenario JSONL instances. If given a folder, then
                            all JSONL files in the folder will be loaded and run.
        n_repeats (int):    The number of times each scenario instance will be repeated
        is_native (bool):   True if the scenario should be run locally rather than in Docker (proceed with caution!)
        results_dir (path): The folder were results will be saved.
    """

    files: List[str] = []

    # Figure out which files or folders we are working with
    if scenario == "-" or os.path.isfile(scenario):
        files.append(scenario)
    elif os.path.isdir(scenario):
        for f in os.listdir(scenario):
            scenario_file = os.path.join(scenario, f)

            if not os.path.isfile(scenario_file):
                continue

            if not scenario_file.lower().endswith(".jsonl"):
                continue

            files.append(scenario_file)
    else:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), scenario)

    # Run all the scenario files
    for scenario_file in files:
        scenario_name: Optional[str] = None
        scenario_dir: Optional[str] = None
        file_handle = None

        # stdin
        if scenario_file == "-":
            scenario_name = "stdin"
            scenario_dir = "."
            file_handle = sys.stdin
        else:
            scenario_name_parts = os.path.basename(scenario_file).split(".")
            scenario_name_parts.pop()
            scenario_name = ".".join(scenario_name_parts)
            scenario_dir = os.path.dirname(os.path.realpath(scenario_file))
            file_handle = open(scenario_file, "rt")

        # Read all the lines, then subsample if needed
        lines = [line for line in file_handle]
        if subsample is not None:
            # How many lines are we sampling
            n = 0
            # It's a proportion
            if 0 <= subsample < 1:
                n = int(len(lines) * subsample + 0.5)
            # It's a raw count
            else:
                n = int(subsample)
            n = max(0, min(n, len(lines)))
            lines = subsample_rng.sample(lines, n)

        for line in lines:
            instance = json.loads(line)

            # Create a folder to store the results
            # Results base
            if not os.path.isdir(results_dir):
                os.mkdir(results_dir)

            # Results for the scenario
            results_scenario = os.path.join(results_dir, scenario_name)
            if not os.path.isdir(results_scenario):
                os.mkdir(results_scenario)

            # Results for the instance
            results_instance = os.path.join(results_scenario, instance["id"])
            if not os.path.isdir(results_instance):
                os.mkdir(results_instance)

            # Results for the repeats
            for i in range(0, n_repeats):
                results_repetition = os.path.join(results_instance, str(i))

                # Skip it if it already exists
                if os.path.isdir(results_repetition):
                    print(f"Found folder {results_repetition} ... Skipping.")
                    continue
                print(f"Running scenario {results_repetition}")

                # Expand the scenario
                expand_scenario(scenario_dir, instance, results_repetition, config_file)

                # Prepare the environment (keys/values that need to be added)
                env = get_scenario_env(token_provider=token_provider, env_file=env_file)

                # Run the scenario
                if is_native:
                    run_scenario_natively(results_repetition, env)
                else:
                    run_scenario_in_docker(
                        results_repetition,
                        env,
                        docker_image=docker_image,
                    )

        # Close regular files
        if scenario_file != "-":
            file_handle.close()