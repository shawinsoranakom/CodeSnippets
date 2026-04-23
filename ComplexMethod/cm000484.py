def from_db(_graph_exec: AgentGraphExecution):
        if _graph_exec.NodeExecutions is None:
            raise ValueError("Node executions must be included in query")

        graph_exec = GraphExecutionMeta.from_db(_graph_exec)

        complete_node_executions = sorted(
            [
                NodeExecutionResult.from_db(ne, _graph_exec.userId)
                for ne in _graph_exec.NodeExecutions
                if ne.executionStatus != ExecutionStatus.INCOMPLETE
            ],
            key=lambda ne: (ne.queue_time is None, ne.queue_time or ne.add_time),
        )

        inputs = {
            **(
                graph_exec.inputs
                or {
                    # fallback: extract inputs from Agent Input Blocks
                    exec.input_data["name"]: exec.input_data.get("value")
                    for exec in complete_node_executions
                    if (
                        (block := get_block(exec.block_id))
                        and block.block_type == BlockType.INPUT
                        and "name" in exec.input_data
                    )
                }
            ),
            **{
                # input from webhook-triggered block
                "payload": exec.input_data.get("payload")
                for exec in complete_node_executions
                if (
                    (block := get_block(exec.block_id))
                    and block.block_type
                    in [BlockType.WEBHOOK, BlockType.WEBHOOK_MANUAL]
                )
            },
        }

        outputs: CompletedBlockOutput = defaultdict(list)
        for exec in complete_node_executions:
            if (
                (block := get_block(exec.block_id))
                and block.block_type == BlockType.OUTPUT
                and "name" in exec.input_data
            ):
                outputs[exec.input_data["name"]].append(exec.input_data.get("value"))

        return GraphExecution(
            **{
                field_name: getattr(graph_exec, field_name)
                for field_name in GraphExecutionMeta.model_fields
                if field_name != "inputs"
            },
            inputs=inputs,
            outputs=outputs,
        )