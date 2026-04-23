def main(
    project_path: str = typer.Argument(".", help="path"),
    model: str = typer.Option(
        os.environ.get("MODEL_NAME", "gpt-4o"), "--model", "-m", help="model id string"
    ),
    temperature: float = typer.Option(
        0.1,
        "--temperature",
        "-t",
        help="Controls randomness: lower values for more focused, deterministic outputs",
    ),
    improve_mode: bool = typer.Option(
        False,
        "--improve",
        "-i",
        help="Improve an existing project by modifying the files.",
    ),
    lite_mode: bool = typer.Option(
        False,
        "--lite",
        "-l",
        help="Lite mode: run a generation using only the main prompt.",
    ),
    clarify_mode: bool = typer.Option(
        False,
        "--clarify",
        "-c",
        help="Clarify mode - discuss specification with AI before implementation.",
    ),
    self_heal_mode: bool = typer.Option(
        False,
        "--self-heal",
        "-sh",
        help="Self-heal mode - fix the code by itself when it fails.",
    ),
    azure_endpoint: str = typer.Option(
        "",
        "--azure",
        "-a",
        help="""Endpoint for your Azure OpenAI Service (https://xx.openai.azure.com).
            In that case, the given model is the deployment name chosen in the Azure AI Studio.""",
    ),
    use_custom_preprompts: bool = typer.Option(
        False,
        "--use-custom-preprompts",
        help="""Use your project's custom preprompts instead of the default ones.
          Copies all original preprompts to the project's workspace if they don't exist there.""",
    ),
    llm_via_clipboard: bool = typer.Option(
        False,
        "--llm-via-clipboard",
        help="Use the clipboard to communicate with the AI.",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging for debugging."
    ),
    debug: bool = typer.Option(
        False, "--debug", "-d", help="Enable debug mode for debugging."
    ),
    prompt_file: str = typer.Option(
        "prompt",
        "--prompt_file",
        help="Relative path to a text file containing a prompt.",
    ),
    entrypoint_prompt_file: str = typer.Option(
        "",
        "--entrypoint_prompt",
        help="Relative path to a text file containing a file that specifies requirements for you entrypoint.",
    ),
    image_directory: str = typer.Option(
        "",
        "--image_directory",
        help="Relative path to a folder containing images.",
    ),
    use_cache: bool = typer.Option(
        False,
        "--use_cache",
        help="Speeds up computations and saves tokens when running the same prompt multiple times by caching the LLM response.",
    ),
    skip_file_selection: bool = typer.Option(
        False,
        "--skip-file-selection",
        "-s",
        help="Skip interactive file selection in improve mode and use the generated TOML file directly.",
    ),
    no_execution: bool = typer.Option(
        False,
        "--no_execution",
        help="Run setup but to not call LLM or write any code. For testing purposes.",
    ),
    sysinfo: bool = typer.Option(
        False,
        "--sysinfo",
        help="Output system information for debugging",
    ),
    diff_timeout: int = typer.Option(
        3,
        "--diff_timeout",
        help="Diff regexp timeout. Default: 3. Increase if regexp search timeouts.",
    ),
):
    """
    The main entry point for the CLI tool that generates or improves a project.

    This function sets up the CLI tool, loads environment variables, initializes
    the AI, and processes the user's request to generate or improve a project
    based on the provided arguments.

    Parameters
    ----------
    project_path : str
        The file path to the project directory.
    model : str
        The model ID string for the AI.
    temperature : float
        The temperature setting for the AI's responses.
    improve_mode : bool
        Flag indicating whether to improve an existing project.
    lite_mode : bool
        Flag indicating whether to run in lite mode.
    clarify_mode : bool
        Flag indicating whether to discuss specifications with AI before implementation.
    self_heal_mode : bool
        Flag indicating whether to enable self-healing mode.
    azure_endpoint : str
        The endpoint for Azure OpenAI services.
    use_custom_preprompts : bool
        Flag indicating whether to use custom preprompts.
    prompt_file : str
        Relative path to a text file containing a prompt.
    entrypoint_prompt_file: str
        Relative path to a text file containing a file that specifies requirements for you entrypoint.
    image_directory: str
        Relative path to a folder containing images.
    use_cache: bool
        Speeds up computations and saves tokens when running the same prompt multiple times by caching the LLM response.
    verbose : bool
        Flag indicating whether to enable verbose logging.
    skip_file_selection: bool
        Skip interactive file selection in improve mode and use the generated TOML file directly
    no_execution: bool
        Run setup but to not call LLM or write any code. For testing purposes.
    sysinfo: bool
        Flag indicating whether to output system information for debugging.

    Returns
    -------
    None
    """

    if debug:
        import pdb

        sys.excepthook = lambda *_: pdb.pm()

    if sysinfo:
        sys_info = get_system_info()
        for key, value in sys_info.items():
            print(f"{key}: {value}")
        raise typer.Exit()

    # Validate arguments
    if improve_mode and (clarify_mode or lite_mode):
        typer.echo("Error: Clarify and lite mode are not compatible with improve mode.")
        raise typer.Exit(code=1)

    # Set up logging
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    if use_cache:
        set_llm_cache(SQLiteCache(database_path=".langchain.db"))
    if improve_mode:
        assert not (
            clarify_mode or lite_mode
        ), "Clarify and lite mode are not active for improve mode"

    load_env_if_needed()

    if llm_via_clipboard:
        ai = ClipboardAI()
    else:
        ai = AI(
            model_name=model,
            temperature=temperature,
            azure_endpoint=azure_endpoint,
        )

    path = Path(project_path)
    print("Running gpt-engineer in", path.absolute(), "\n")

    prompt = load_prompt(
        DiskMemory(path),
        improve_mode,
        prompt_file,
        image_directory,
        entrypoint_prompt_file,
    )

    # todo: if ai.vision is false and not llm_via_clipboard - ask if they would like to use gpt-4-vision-preview instead? If so recreate AI
    if not ai.vision:
        prompt.image_urls = None

    # configure generation function
    if clarify_mode:
        code_gen_fn = clarified_gen
    elif lite_mode:
        code_gen_fn = lite_gen
    else:
        code_gen_fn = gen_code

    # configure execution function
    if self_heal_mode:
        execution_fn = self_heal
    else:
        execution_fn = execute_entrypoint

    preprompts_holder = PrepromptsHolder(
        get_preprompts_path(use_custom_preprompts, Path(project_path))
    )

    memory = DiskMemory(memory_path(project_path))
    memory.archive_logs()

    execution_env = DiskExecutionEnv()
    agent = CliAgent.with_default_config(
        memory,
        execution_env,
        ai=ai,
        code_gen_fn=code_gen_fn,
        improve_fn=improve_fn,
        process_code_fn=execution_fn,
        preprompts_holder=preprompts_holder,
    )

    files = FileStore(project_path)
    if not no_execution:
        if improve_mode:
            files_dict_before, is_linting = FileSelector(project_path).ask_for_files(
                skip_file_selection=skip_file_selection
            )

            # lint the code
            if is_linting:
                files_dict_before = files.linting(files_dict_before)

            files_dict = handle_improve_mode(
                prompt, agent, memory, files_dict_before, diff_timeout=diff_timeout
            )
            if not files_dict or files_dict_before == files_dict:
                print(
                    f"No changes applied. Could you please upload the debug_log_file.txt in {memory.path}/logs folder in a github issue?"
                )

            else:
                print("\nChanges to be made:")
                compare(files_dict_before, files_dict)

                print()
                print(colored("Do you want to apply these changes?", "light_green"))
                if not prompt_yesno():
                    files_dict = files_dict_before

        else:
            files_dict = agent.init(prompt)
            # collect user feedback if user consents
            config = (code_gen_fn.__name__, execution_fn.__name__)
            collect_and_send_human_review(prompt, model, temperature, config, memory)

        stage_uncommitted_to_git(path, files_dict, improve_mode)

        files.push(files_dict)

    if ai.token_usage_log.is_openai_model():
        print("Total api cost: $ ", ai.token_usage_log.usage_cost())
    elif os.getenv("LOCAL_MODEL"):
        print("Total api cost: $ 0.0 since we are using local LLM.")
    else:
        print("Total tokens used: ", ai.token_usage_log.total_tokens())