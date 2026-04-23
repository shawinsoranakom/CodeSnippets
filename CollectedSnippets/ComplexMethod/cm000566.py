async def _run(
        self,
        graph_id: str,
        graph_version: int,
        graph_exec_id: str,
        user_id: str,
        logger: "LogMetadata",
    ) -> BlockOutput:

        from backend.blocks import get_block
        from backend.data.execution import ExecutionEventType
        from backend.executor import utils as execution_utils

        event_bus = execution_utils.get_async_execution_event_bus()

        log_id = f"Graph #{graph_id}-V{graph_version}, exec-id: {graph_exec_id}"
        logger.info(f"Starting execution of {log_id}")
        yielded_node_exec_ids = set()

        async for event in event_bus.listen(
            user_id=user_id,
            graph_id=graph_id,
            graph_exec_id=graph_exec_id,
        ):
            if event.status not in [
                ExecutionStatus.COMPLETED,
                ExecutionStatus.TERMINATED,
                ExecutionStatus.FAILED,
            ]:
                logger.info(
                    f"Execution {log_id} skipping event {event.event_type} status={event.status} "
                    f"node={getattr(event, 'node_exec_id', '?')}"
                )
                continue

            if event.event_type == ExecutionEventType.GRAPH_EXEC_UPDATE:
                # If the graph execution is COMPLETED, TERMINATED, or FAILED,
                # we can stop listening for further events.
                logger.info(
                    f"Execution {log_id} graph completed with status {event.status}, "
                    f"yielded {len(yielded_node_exec_ids)} outputs"
                )
                self.merge_stats(
                    NodeExecutionStats(
                        extra_cost=event.stats.cost if event.stats else 0,
                        extra_steps=event.stats.node_exec_count if event.stats else 0,
                    )
                )
                break

            logger.debug(
                f"Execution {log_id} produced input {event.input_data} output {event.output_data}"
            )

            if event.node_exec_id in yielded_node_exec_ids:
                logger.warning(
                    f"{log_id} received duplicate event for node execution {event.node_exec_id}"
                )
                continue
            else:
                yielded_node_exec_ids.add(event.node_exec_id)

            if not event.block_id:
                logger.warning(f"{log_id} received event without block_id {event}")
                continue

            block = get_block(event.block_id)
            if not block or block.block_type != BlockType.OUTPUT:
                continue

            output_name = event.input_data.get("name")
            if not output_name:
                logger.warning(f"{log_id} produced an output with no name {event}")
                continue

            for output_data in event.output_data.get("output", []):
                logger.debug(
                    f"Execution {log_id} produced {output_name}: {output_data}"
                )
                yield output_name, output_data