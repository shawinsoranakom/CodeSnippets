async def main(num_teams: int, num_answers: int) -> None:

    # Load model configuration and create the model client.
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    orchestrator_client = ChatCompletionClient.load_component(config["orchestrator_client"])
    coder_client = ChatCompletionClient.load_component(config["coder_client"])
    web_surfer_client = ChatCompletionClient.load_component(config["web_surfer_client"])
    file_surfer_client = ChatCompletionClient.load_component(config["file_surfer_client"])

    # Read the prompt
    prompt = ""
    with open("prompt.txt", "rt") as fh:
        prompt = fh.read().strip()
    filename = "__FILE_NAME__".strip()

    # Prepare the prompt
    filename_prompt = ""
    if len(filename) > 0:
        filename_prompt = f"The question is about a file, document or image, which can be accessed by the filename '{filename}' in the current working directory."
    task = f"{prompt}\n\n{filename_prompt}"

    # Reset logs directory (remove all files in it)
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        shutil.rmtree(logs_dir)

    teams = []
    async_tasks = []
    tokens = []
    for team_idx in range(num_teams):
        # Set up the team
        coder = MagenticOneCoderAgent(
            "Assistant",
            model_client = coder_client,
        )

        executor = CodeExecutorAgent("ComputerTerminal", code_executor=LocalCommandLineCodeExecutor())

        file_surfer = FileSurfer(
            name="FileSurfer",
            model_client = file_surfer_client,
        )

        web_surfer = MultimodalWebSurfer(
            name="WebSurfer",
            model_client = web_surfer_client,
            downloads_folder=os.getcwd(),
            debug_dir=logs_dir,
            to_save_screenshots=True,
        )
        team = MagenticOneGroupChat(
            [coder, executor, file_surfer, web_surfer],
            model_client=orchestrator_client,
            max_turns=30,
            final_answer_prompt= f""",
We have completed the following task:

{prompt}

The above messages contain the conversation that took place to complete the task.
Read the above conversation and output a FINAL ANSWER to the question.
To output the final answer, use the following template: FINAL ANSWER: [YOUR FINAL ANSWER]
Your FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings.
ADDITIONALLY, your FINAL ANSWER MUST adhere to any formatting instructions specified in the original question (e.g., alphabetization, sequencing, units, rounding, decimal places, etc.)
If you are asked for a number, express it numerically (i.e., with digits rather than words), don't use commas, and don't include units such as $ or percent signs unless specified otherwise.
If you are asked for a string, don't use articles or abbreviations (e.g. for cities), unless specified otherwise. Don't output any final sentence punctuation such as '.', '!', or '?'.
If you are asked for a comma separated list, apply the above rules depending on whether the elements are numbers or strings.
""".strip()
        )
        teams.append(team)
        cancellation_token = CancellationToken()
        tokens.append(cancellation_token)
        logfile = open(f"console_log_{team_idx}.txt", "w")
        team_agentchat_logger = logging.getLogger(f"{AGENTCHAT_EVENT_LOGGER_NAME}.team{team_idx}")
        team_core_logger = logging.getLogger(f"{CORE_EVENT_LOGGER_NAME}.team{team_idx}")
        team_log_handler = LogHandler(f"log_{team_idx}.jsonl", print_message=False)
        team_agentchat_logger.addHandler(team_log_handler)
        team_core_logger.addHandler(team_log_handler)
        async_task = asyncio.create_task(
            run_team(team, team_idx, task, cancellation_token, logfile)
        )
        async_tasks.append(async_task)

    # Wait until at least num_answers tasks have completed.
    team_results = {}
    for future in asyncio.as_completed(async_tasks):
        try:
            team_id, result = await future
            team_results[team_id] = result
        except Exception as e:
            # Optionally log exception.
            print(f"Task raised an exception: {e}")
        if len(team_results) >= num_answers:
            break

    # Cancel any pending teams.
    for task, token in zip(async_tasks, tokens):
        if not task.done():
            token.cancel()
    # Await all tasks to handle cancellation gracefully.
    await asyncio.gather(*async_tasks, return_exceptions=True)

    print("len(team_results):", len(team_results))
    final_answer = await aggregate_final_answer(prompt, orchestrator_client, team_results)
    print(final_answer)