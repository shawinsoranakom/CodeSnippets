def get_schedule_ops(
    schedule: str | type[_PipelineSchedule],
    pp_degree: int,
    num_microbatches: int,
    num_stages_per_rank: int | None = None,
    add_spacing: bool = False,
    with_comms: bool = False,
) -> list[list[_Action | None]]:
    """
    Get all actions for a given schedule, pp_degree, and num_microbatches. The actions are returned in a list of lists
    where each inner list represents a rank and each element in the inner list represents an action.

    The schedule can be specified as a string which is passed into get_schedule_class() or a _PipelineSchedule instance.
    """
    if add_spacing and with_comms:
        raise ValueError("Cannot add spacing and view comms at the same time")

    if isinstance(schedule, str):
        schedule_class = get_schedule_class(schedule)
    elif issubclass(schedule, _PipelineSchedule):
        schedule_class = schedule
    else:
        raise ValueError(f"Invalid schedule: {schedule}")

    # Create a mock of the PipelineStage class
    mock_pipeline_stage = mock.create_autospec(PipelineStage, instance=True)
    # Set the return values for group_rank and group_size methods
    mock_pipeline_stage.group_rank = 0
    mock_pipeline_stage.group_size = pp_degree
    mock_pipeline_stage.submod = None

    # Check num_stages_per_rank is valid
    if issubclass(schedule_class, PipelineScheduleSingle):
        if num_stages_per_rank is None:
            num_stages_per_rank = 1
        if not num_stages_per_rank == 1:
            raise AssertionError(
                f"Expected num_stages_per_rank to be 1, got {num_stages_per_rank}"
            )
        stages = mock_pipeline_stage
        stages.num_stages = num_stages_per_rank * pp_degree
    elif issubclass(schedule_class, PipelineScheduleMulti):
        if num_stages_per_rank is None:
            num_stages_per_rank = 2
        if not num_stages_per_rank >= 2:
            raise AssertionError(
                f"Expected num_stages_per_rank >= 2, got {num_stages_per_rank}"
            )
        stages = [mock_pipeline_stage for _ in range(num_stages_per_rank)]
        for stage in stages:
            stage.num_stages = num_stages_per_rank * pp_degree

    else:
        raise ValueError(f"Invalid schedule: {schedule_class}")

    # Instantiate the schedule class
    # pyrefly: ignore [bad-argument-type]
    schedule_instance = schedule_class(stages, num_microbatches)
    if schedule_instance.pipeline_order is None:
        raise AssertionError("Expected pipeline_order to not be None")

    # Convert to List[List[_Action]]
    all_actions: list[list[_Action | None]] = []
    if with_comms:
        runtime = _PipelineScheduleRuntime(stages, num_microbatches)
        runtime._prepare_schedule_with_comms(schedule_instance.pipeline_order)
        for rank in range(pp_degree):
            all_actions.append(list(runtime.pipeline_order_with_comms[rank]))
    else:
        for rank in range(pp_degree):
            all_actions.append(schedule_instance.pipeline_order[rank])

    # Add spacing
    if add_spacing:
        # remove all Nones, then respace
        # TODO: later we can change this at the schedule creation level to not use Nones
        all_actions = [
            [action for action in rank if action is not None] for rank in all_actions
        ]
        all_actions = add_schedule_op_spacing(all_actions)

    # Return the pipeline order
    return all_actions