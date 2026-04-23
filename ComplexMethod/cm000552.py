async def _execute_single_tool_with_manager(
        self,
        tool_info: ToolInfo,
        execution_params: ExecutionParams,
        execution_processor: "ExecutionProcessor",
        *,
        responses_api: bool = False,
    ) -> dict:
        """Execute a single tool using the execution manager for proper integration."""
        # Lazy imports to avoid circular dependencies
        from backend.data.execution import NodeExecutionEntry

        tool_call = tool_info.tool_call
        tool_def = tool_info.tool_def
        raw_input_data = tool_info.input_data

        # Get sink node and field mapping
        sink_node_id = tool_def["function"]["_sink_node_id"]

        # Use proper database operations for tool execution
        db_client = get_database_manager_async_client()

        # Get target node
        target_node = await db_client.get_node(sink_node_id)
        if not target_node:
            raise ValueError(f"Target node {sink_node_id} not found")

        # Create proper node execution using upsert_execution_input
        node_exec_result = None
        final_input_data = None

        # Merge static defaults from the target node with LLM-provided inputs.
        # The LLM only passes values it decides to fill (e.g., "value"), but
        # static defaults like "name" on Agent Output Blocks must be included
        # so the execution record is complete for from_db() reconstruction.
        merged_input_data = {**target_node.input_default, **raw_input_data}

        # Add all inputs to the execution
        if not merged_input_data:
            raise ValueError(f"Tool call has no input data: {tool_call}")

        for input_name, input_value in merged_input_data.items():
            node_exec_result, final_input_data = await db_client.upsert_execution_input(
                node_id=sink_node_id,
                graph_exec_id=execution_params.graph_exec_id,
                input_name=input_name,
                input_data=input_value,
            )

        if node_exec_result is None:
            raise RuntimeError(
                f"upsert_execution_input returned None for node {sink_node_id}"
            )

        # Create NodeExecutionEntry for execution manager
        node_exec_entry = NodeExecutionEntry(
            user_id=execution_params.user_id,
            graph_exec_id=execution_params.graph_exec_id,
            graph_id=execution_params.graph_id,
            graph_version=execution_params.graph_version,
            node_exec_id=node_exec_result.node_exec_id,
            node_id=sink_node_id,
            block_id=target_node.block_id,
            inputs=final_input_data or {},
            execution_context=execution_params.execution_context,
        )

        # Use the execution manager to execute the tool node
        try:
            # Get NodeExecutionProgress from the execution manager's running nodes
            node_exec_progress = execution_processor.running_node_execution[
                sink_node_id
            ]

            # Use the execution manager's own graph stats
            graph_stats_pair = (
                execution_processor.execution_stats,
                execution_processor.execution_stats_lock,
            )

            # Create a completed future for the task tracking system
            node_exec_future = Future()
            node_exec_progress.add_task(
                node_exec_id=node_exec_result.node_exec_id,
                task=node_exec_future,
            )

            # Execute the node directly since we're in the Orchestrator context.
            # Wrap in try/except so the future is always resolved, even on
            # error — an unresolved Future would block anything awaiting it.
            #
            # on_node_execution is decorated with @async_error_logged(swallow=True),
            # which catches BaseException and returns None rather than raising.
            # Treat a None return as a failure: set_exception so the future
            # carries an error state rather than a None result, and return an
            # error response so the LLM knows the tool failed.
            try:
                tool_node_stats = await execution_processor.on_node_execution(
                    node_exec=node_exec_entry,
                    node_exec_progress=node_exec_progress,
                    nodes_input_masks=None,
                    graph_stats_pair=graph_stats_pair,
                )
                if tool_node_stats is None:
                    nil_err = RuntimeError(
                        f"on_node_execution returned None for node {sink_node_id} "
                        "(error was swallowed by @async_error_logged)"
                    )
                    node_exec_future.set_exception(nil_err)
                    resp = _create_tool_response(
                        tool_call.id,
                        "Tool execution returned no result",
                        responses_api=responses_api,
                    )
                    resp["_is_error"] = True
                    return resp
                node_exec_future.set_result(tool_node_stats)
            except Exception as exec_err:
                node_exec_future.set_exception(exec_err)
                raise

            # Charge user credits AFTER successful tool execution. Tools
            # spawned by the orchestrator bypass the main execution queue
            # (where _charge_usage is called), so we must charge here to
            # avoid free tool execution. Charging post-completion (vs.
            # pre-execution) avoids billing users for failed tool calls.
            # Skipped for dry runs.
            #
            # `error is None` intentionally excludes both Exception and
            # BaseException subclasses (e.g. CancelledError) so cancelled
            # or terminated tool runs are not billed.
            #
            # Billing errors (including non-balance exceptions) are kept
            # in a separate try/except so they are never silently swallowed
            # by the generic tool-error handler below.
            if (
                not execution_params.execution_context.dry_run
                and tool_node_stats.error is None
            ):
                try:
                    tool_cost, _ = await execution_processor.charge_node_usage(
                        node_exec_entry,
                    )
                except InsufficientBalanceError:
                    # IBE must propagate — see OrchestratorBlock class docstring.
                    # Log the billing failure here so the discarded tool result
                    # is traceable before the loop aborts.
                    logger.warning(
                        "Insufficient balance charging for tool node %s after "
                        "successful execution; agent loop will be aborted",
                        sink_node_id,
                    )
                    raise
                except Exception:
                    # Non-billing charge failures (DB outage, network, etc.)
                    # must NOT propagate to the outer except handler because
                    # the tool itself succeeded. Re-raising would mark the
                    # tool as failed (_is_error=True), causing the LLM to
                    # retry side-effectful operations. Log and continue.
                    logger.exception(
                        "Unexpected error charging for tool node %s; "
                        "tool execution was successful",
                        sink_node_id,
                    )
                    tool_cost = 0
                if tool_cost > 0:
                    self.merge_stats(NodeExecutionStats(extra_cost=tool_cost))

            # Get outputs from database after execution completes using database manager client
            node_outputs = await db_client.get_execution_outputs_by_node_exec_id(
                node_exec_result.node_exec_id
            )

            # Create tool response
            tool_response_content = (
                json.dumps(node_outputs)
                if node_outputs
                else "Tool executed successfully"
            )
            resp = _create_tool_response(
                tool_call.id, tool_response_content, responses_api=responses_api
            )
            resp["_is_error"] = False
            return resp

        except InsufficientBalanceError:
            # IBE must propagate — see class docstring.
            raise
        except Exception as e:
            logger.warning("Tool execution with manager failed: %s", e, exc_info=True)
            # Return a generic error to the LLM — internal exception messages
            # may contain server paths, DB details, or infrastructure info.
            resp = _create_tool_response(
                tool_call.id,
                "Tool execution failed due to an internal error",
                responses_api=responses_api,
            )
            resp["_is_error"] = True
            return resp