def _calculate_agent_status(
    executions: list[prisma.models.AgentGraphExecution],
    recent_threshold: datetime.datetime,
) -> AgentStatusResult:
    """
    Helper function to determine the overall agent status and whether there
    is new output (i.e., completed runs within the recent threshold).

    :param executions: A list of AgentGraphExecution objects.
    :param recent_threshold: A datetime; any execution after this indicates new output.
    :return: (AgentStatus, new_output_flag)
    """

    if not executions:
        return AgentStatusResult(status=LibraryAgentStatus.COMPLETED, new_output=False)

    # Track how many times each execution status appears
    status_counts = {status: 0 for status in prisma.enums.AgentExecutionStatus}
    new_output = False

    for execution in executions:
        # Check if there's a completed run more recent than `recent_threshold`
        if execution.createdAt >= recent_threshold:
            if execution.executionStatus == prisma.enums.AgentExecutionStatus.COMPLETED:
                new_output = True
        status_counts[execution.executionStatus] += 1

    # Determine the final status based on counts
    if status_counts[prisma.enums.AgentExecutionStatus.FAILED] > 0:
        return AgentStatusResult(status=LibraryAgentStatus.ERROR, new_output=new_output)
    elif status_counts[prisma.enums.AgentExecutionStatus.QUEUED] > 0:
        return AgentStatusResult(
            status=LibraryAgentStatus.WAITING, new_output=new_output
        )
    elif status_counts[prisma.enums.AgentExecutionStatus.RUNNING] > 0:
        return AgentStatusResult(
            status=LibraryAgentStatus.HEALTHY, new_output=new_output
        )
    else:
        return AgentStatusResult(
            status=LibraryAgentStatus.COMPLETED, new_output=new_output
        )
