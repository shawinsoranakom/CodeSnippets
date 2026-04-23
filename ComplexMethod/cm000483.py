def from_db(_graph_exec: AgentGraphExecution):
        start_time = _graph_exec.startedAt
        end_time = _graph_exec.endedAt

        try:
            stats = GraphExecutionStats.model_validate(_graph_exec.stats)
        except ValueError as e:
            if _graph_exec.stats is not None:
                logger.warning(
                    "Failed to parse invalid graph execution stats "
                    f"{_graph_exec.stats}: {e}"
                )
            stats = None

        return GraphExecutionMeta(
            id=_graph_exec.id,
            user_id=_graph_exec.userId,
            graph_id=_graph_exec.agentGraphId,
            graph_version=_graph_exec.agentGraphVersion,
            inputs=cast(GraphInput | None, _graph_exec.inputs),
            credential_inputs=(
                {
                    name: CredentialsMetaInput.model_validate(cmi)
                    for name, cmi in cast(dict, _graph_exec.credentialInputs).items()
                }
                if _graph_exec.credentialInputs
                else None
            ),
            nodes_input_masks=cast(
                dict[str, BlockInput] | None, _graph_exec.nodesInputMasks
            ),
            preset_id=_graph_exec.agentPresetId,
            status=ExecutionStatus(_graph_exec.executionStatus),
            started_at=start_time,
            ended_at=end_time,
            stats=(
                GraphExecutionMeta.Stats(
                    cost=stats.cost,
                    duration=stats.walltime,
                    duration_cpu_only=stats.cputime,
                    node_exec_time=stats.nodes_walltime,
                    node_exec_time_cpu_only=stats.nodes_cputime,
                    node_exec_count=stats.node_count,
                    node_error_count=stats.node_error_count,
                    error=(
                        str(stats.error)
                        if isinstance(stats.error, Exception)
                        else stats.error
                    ),
                    activity_status=stats.activity_status,
                    correctness_score=stats.correctness_score,
                )
                if stats
                else None
            ),
            is_shared=_graph_exec.isShared,
            share_token=_graph_exec.shareToken,
            is_dry_run=stats.is_dry_run if stats else False,
        )