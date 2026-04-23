async def run_interaction_loop(
    agent: "Agent",
    ui_provider: Optional["UIProvider"] = None,
) -> None:
    """Run the main interaction loop for the agent.

    Args:
        agent: The agent to run the interaction loop for.
        ui_provider: Optional UI provider for displaying output.
                    If not provided, a terminal provider will be created.

    Returns:
        None
    """
    # These contain both application config and agent config, so grab them here.
    app_config = agent.app_config
    ai_profile = agent.state.ai_profile
    logger = logging.getLogger(__name__)

    # Create default UI provider if not provided
    if ui_provider is None:
        ui_provider = create_ui_provider(
            plain_output=app_config.logging.plain_console_output,
        )
    assert ui_provider is not None  # Satisfy type checker

    cycle_budget = cycles_remaining = _get_cycle_budget(
        app_config.continuous_mode, app_config.continuous_limit
    )
    # Keep spinner for signal handler compatibility (but use UI provider in loop)
    spinner = Spinner(
        "Thinking...", plain_output=app_config.logging.plain_console_output
    )
    stop_reason = None

    def graceful_agent_interrupt(signum: int, frame: Optional[FrameType]) -> None:
        nonlocal cycles_remaining, stop_reason
        if stop_reason:
            logger.error("Quitting immediately...")
            sys.exit()
        if cycles_remaining in [0, 1]:
            logger.warning("Interrupt signal received: shutting down gracefully.")
            logger.warning(
                "Press Ctrl+C again if you want to stop AutoGPT immediately."
            )
            stop_reason = AgentTerminated("Interrupt signal received")
        else:
            restart_spinner = spinner.running
            if spinner.running:
                spinner.stop()

            logger.error(
                "Interrupt signal received: stopping continuous command execution."
            )
            cycles_remaining = 1
            if restart_spinner:
                spinner.start()

    def handle_stop_signal() -> None:
        if stop_reason:
            raise stop_reason

    # Set up an interrupt signal for the agent.
    signal.signal(signal.SIGINT, graceful_agent_interrupt)

    #########################
    # Application Main Loop #
    #########################

    # Keep track of consecutive failures of the agent
    consecutive_failures = 0

    while cycles_remaining > 0:
        logger.debug(f"Cycle budget: {cycle_budget}; remaining: {cycles_remaining}")

        ########
        # Plan #
        ########
        handle_stop_signal()
        # Have the agent determine the next action to take.
        if not (_ep := agent.event_history.current_episode) or _ep.result:
            async with ui_provider.show_spinner("Thinking..."):
                try:
                    action_proposal = await agent.propose_action()
                except InvalidAgentResponseError as e:
                    logger.warning(f"The agent's thoughts could not be parsed: {e}")
                    consecutive_failures += 1
                    if consecutive_failures >= 3:
                        logger.error(
                            "The agent failed to output valid thoughts"
                            f" {consecutive_failures} times in a row. Terminating..."
                        )
                        raise AgentTerminated(
                            "The agent failed to output valid thoughts"
                            f" {consecutive_failures} times in a row."
                        )
                    continue
        else:
            action_proposal = _ep.action

        consecutive_failures = 0

        ###############
        # Update User #
        ###############
        # Display the assistant's thoughts and the next command via UI provider
        await ui_provider.display_thoughts(
            ai_name=ai_profile.ai_name,
            thoughts=action_proposal.thoughts,
            speak_mode=app_config.tts_config.speak_mode,
        )

        # Note: Command details are shown in the approval prompt, so we don't
        # display them separately here to avoid redundancy

        # Permission manager handles per-command approval during execute()
        handle_stop_signal()

        ###################
        # Execute Command #
        ###################
        if not action_proposal.use_tool:
            continue

        handle_stop_signal()

        # Execute the command. Permission manager will prompt user if needed.
        # If user denies with feedback, the agent will receive it via
        # ActionInterruptedByHuman. If user approves with feedback, command
        # executes and feedback is appended to history.
        try:
            result = await agent.execute(action_proposal)
        except AgentFinished as e:
            # Handle finish command
            if app_config.noninteractive_mode:
                # Non-interactive: exit (preserve benchmark behavior)
                logger.info(f"Agent finished: {e.message}")
                return

            # Interactive mode: show panel and prompt for continuation
            next_task = await ui_provider.prompt_finish_continuation(
                summary=e.message,
                suggested_next_task=e.suggested_next_task,
            )

            if not next_task.strip():
                # Empty input = exit
                logger.info("User chose to exit after task completion.")
                return

            # Start new task in same workspace
            agent.state.task = next_task
            agent.event_history.episodes.clear()  # Clear history for fresh context
            agent.event_history.cursor = 0

            # Reset cycle budget for new task
            cycles_remaining = _get_cycle_budget(
                app_config.continuous_mode, app_config.continuous_limit
            )

            logger.info(f"Starting new task: {next_task}")
            continue

        if result.status != "interrupted_by_human":
            cycles_remaining -= 1

        # Display user feedback if provided
        if result.status == "interrupted_by_human" and result.feedback:
            await ui_provider.display_message(
                f"Feedback provided: {result.feedback}",
                title="USER:",
            )

        if result.status == "success":
            await ui_provider.display_result(str(result), is_error=False)
        elif result.status == "error":
            error_msg = (
                f"Command {action_proposal.use_tool.name} returned an error: "
                f"{result.error or result.reason}"
            )
            await ui_provider.display_result(error_msg, is_error=True)