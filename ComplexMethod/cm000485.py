def from_db(_node_exec: AgentNodeExecution, user_id: Optional[str] = None):
        try:
            stats = NodeExecutionStats.model_validate(_node_exec.stats or {})
        except (ValueError, ValidationError):
            stats = NodeExecutionStats()

        if stats.cleared_inputs:
            input_data: BlockInput = defaultdict()
            for name, messages in stats.cleared_inputs.items():
                input_data[name] = messages[-1] if messages else ""
        elif _node_exec.executionData:
            input_data = type_utils.convert(_node_exec.executionData, BlockInput)
        else:
            input_data: BlockInput = defaultdict()
            for data in _node_exec.Input or []:
                input_data[data.name] = type_utils.convert(data.data, JsonValue)

        output_data: CompletedBlockOutput = defaultdict(list)

        if stats.cleared_outputs:
            for name, messages in stats.cleared_outputs.items():
                output_data[name].extend(messages)
        else:
            for data in _node_exec.Output or []:
                output_data[data.name].append(type_utils.convert(data.data, JsonValue))

        graph_execution: AgentGraphExecution | None = _node_exec.GraphExecution
        if graph_execution:
            user_id = graph_execution.userId
        elif not user_id:
            raise ValueError(
                "AgentGraphExecution must be included or user_id passed in"
            )

        return NodeExecutionResult(
            user_id=user_id,
            graph_id=graph_execution.agentGraphId if graph_execution else "",
            graph_version=graph_execution.agentGraphVersion if graph_execution else 0,
            graph_exec_id=_node_exec.agentGraphExecutionId,
            block_id=_node_exec.Node.agentBlockId if _node_exec.Node else "",
            node_exec_id=_node_exec.id,
            node_id=_node_exec.agentNodeId,
            status=_node_exec.executionStatus,
            input_data=input_data,
            output_data=output_data,
            add_time=_node_exec.addedTime,
            queue_time=_node_exec.queuedTime,
            start_time=_node_exec.startedTime,
            end_time=_node_exec.endedTime,
        )