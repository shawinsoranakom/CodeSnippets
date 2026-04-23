async def _on_node_execution(
        self,
        node: Node,
        node_exec: NodeExecutionEntry,
        node_exec_progress: NodeExecutionProgress,
        stats: NodeExecutionStats,
        db_client: "DatabaseManagerAsyncClient",
        log_metadata: LogMetadata,
        nodes_input_masks: Optional[NodesInputMasks] = None,
        nodes_to_skip: Optional[set[str]] = None,
    ) -> ExecutionStatus:
        status = ExecutionStatus.RUNNING

        async def persist_output(output_name: str, output_data: Any) -> None:
            await db_client.upsert_execution_output(
                node_exec_id=node_exec.node_exec_id,
                output_name=output_name,
                output_data=output_data,
            )
            if exec_update := await db_client.get_node_execution(
                node_exec.node_exec_id
            ):
                await send_async_execution_update(exec_update)

            node_exec_progress.add_output(
                ExecutionOutputEntry(
                    node=node,
                    node_exec_id=node_exec.node_exec_id,
                    data=(output_name, output_data),
                )
            )

        try:
            log_metadata.info(f"Start node execution {node_exec.node_exec_id}")
            await async_update_node_execution_status(
                db_client=db_client,
                exec_id=node_exec.node_exec_id,
                status=ExecutionStatus.RUNNING,
            )

            async for output_name, output_data in execute_node(
                node=node,
                data=node_exec,
                execution_processor=self,
                execution_stats=stats,
                nodes_input_masks=nodes_input_masks,
                nodes_to_skip=nodes_to_skip,
            ):
                await persist_output(output_name, output_data)

            log_metadata.info(f"Finished node execution {node_exec.node_exec_id}")
            status = ExecutionStatus.COMPLETED

        except BaseException as e:
            stats.error = e

            if isinstance(e, ValueError):
                # Avoid user error being marked as an actual error.
                log_metadata.info(
                    f"Expected failure on node execution {node_exec.node_exec_id}: {type(e).__name__} - {e}"
                )
                status = ExecutionStatus.FAILED
            elif isinstance(e, Exception):
                # If the exception is not a ValueError, it is unexpected.
                log_metadata.exception(
                    f"Unexpected failure on node execution {node_exec.node_exec_id}: {type(e).__name__} - {e}"
                )
                status = ExecutionStatus.FAILED
            else:
                # CancelledError or SystemExit
                log_metadata.warning(
                    f"Interruption error on node execution {node_exec.node_exec_id}: {type(e).__name__}"
                )
                status = ExecutionStatus.TERMINATED

        finally:
            if status == ExecutionStatus.FAILED and stats.error is not None:
                await persist_output(
                    "error", str(stats.error) or type(stats.error).__name__
                )
        return status