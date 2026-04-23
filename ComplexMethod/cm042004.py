async def write_framework(
    use_case_actors: str,
    trd: str,
    additional_technical_requirements: str,
    output_dir: Optional[str] = "",
    investment: float = 20.0,
    context: Optional[Context] = None,
    max_loop: int = 20,
) -> str:
    """
    Run the action to generate a software framework based on the provided TRD and related information.

    Args:
        use_case_actors (str): Description of the use case actors involved.
        trd (str): Technical Requirements Document detailing the requirements.
        additional_technical_requirements (str): Any additional technical requirements.
        output_dir (str, optional): Path to save the software framework files. Default is en empty string.
        investment (float): Budget. Automatically stops optimizing TRD when the budget is overdrawn.
        context (Context, optional): The context configuration. Default is None.
        max_loop(int, optional): Acts as a safety exit valve when cost statistics fail. Default is 20.

    Returns:
        str: The generated software framework as a string of pathnames.

    Example:
        >>> use_case_actors = "- Actor: game player;\\n- System: snake game; \\n- External System: game center;"
        >>> trd = "## TRD\\n..."
        >>> additional_technical_requirements = "Using Java language, ..."
        >>> investment = 15.0
        >>> framework = await write_framework(
        >>>    use_case_actors=use_case_actors,
        >>>    trd=trd,
        >>>    additional_technical_requirements=constraint,
        >>>    investment=investment,
        >>> )
        >>> print(framework)
        [{"path":"balabala", "filename":"...", ...
    """
    context = context or Context(cost_manager=CostManager(max_budget=investment))
    write_framework = WriteFramework(context=context)
    evaluate_framework = EvaluateFramework(context=context)
    is_pass = False
    framework = ""
    evaluation_conclusion = ""
    acknowledgement = await mock_asearch_acknowledgement(use_case_actors)  # Replaced by acknowledgement_repo later.
    loop_count = 0
    output_dir = (
        Path(output_dir)
        if output_dir
        else context.config.workspace.path / (datetime.now().strftime("%Y%m%d%H%M%ST") + uuid.uuid4().hex[0:8])
    )
    file_list = []
    while not is_pass and (context.cost_manager.total_cost < context.cost_manager.max_budget):
        try:
            framework = await write_framework.run(
                use_case_actors=use_case_actors,
                trd=trd,
                acknowledge=acknowledgement,
                legacy_output=framework,
                evaluation_conclusion=evaluation_conclusion,
                additional_technical_requirements=additional_technical_requirements,
            )
        except Exception as e:
            logger.info(f"{e}")
            break
        evaluation = await evaluate_framework.run(
            use_case_actors=use_case_actors,
            trd=trd,
            acknowledge=acknowledgement,
            legacy_output=framework,
            additional_technical_requirements=additional_technical_requirements,
        )
        is_pass = evaluation.is_pass
        evaluation_conclusion = evaluation.conclusion
        loop_count += 1
        logger.info(f"Loop {loop_count}")
        if context.cost_manager.total_cost < 1 and loop_count > max_loop:
            break
        file_list = await save_framework(dir_data=framework, trd=trd, output_dir=output_dir)
        logger.info(f"Output:\n{file_list}")

    return "## Software Framework" + "".join([f"\n- {i}" for i in file_list])