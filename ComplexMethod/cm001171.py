async def tool_call_loop(
    *,
    messages: list[dict[str, Any]],
    tools: Sequence[Any],
    llm_call: LLMCaller,
    execute_tool: ToolExecutor,
    update_conversation: ConversationUpdater,
    max_iterations: int = -1,
    last_iteration_message: str | None = None,
    parallel_tool_calls: bool = True,
) -> AsyncGenerator[ToolCallLoopResult, None]:
    """Run a tool-calling conversation loop as an async generator.

    Yields a ``ToolCallLoopResult`` after each iteration so callers can
    drain buffered events (e.g. streaming text deltas) between iterations.
    The **final** yielded result has ``finished_naturally`` set and contains
    the complete response text.

    Args:
        messages: Initial conversation messages (modified in-place).
        tools: Tool function definitions (OpenAI format).  Accepts any
            sequence of tool dicts, including ``ChatCompletionToolParam``.
        llm_call: Async function to call the LLM. The callback can
            perform streaming internally (e.g. accumulate text deltas
            and collect events) — it just needs to return the final
            ``LLMLoopResponse`` with extracted tool calls.
        execute_tool: Async function to execute a tool call.
        update_conversation: Function to update messages with LLM
            response and tool results.
        max_iterations: Max iterations. -1 = infinite, 0 = no loop
            (immediately yields a "max reached" result).
        last_iteration_message: Optional message to append on the last
            iteration to encourage the model to finish.
        parallel_tool_calls: If True (default), execute multiple tool
            calls from a single LLM response concurrently via
            ``asyncio.gather``.  Set to False when tool calls may have
            ordering dependencies or mutate shared state.

    Yields:
        ToolCallLoopResult after each iteration. Check ``finished_naturally``
        to determine if the loop completed or is still running.
    """
    total_prompt_tokens = 0
    total_completion_tokens = 0
    iteration = 0

    while max_iterations < 0 or iteration < max_iterations:
        iteration += 1

        # On last iteration, add a hint to finish.  Only copy the list
        # when the hint needs to be appended to avoid per-iteration overhead
        # on long conversations.
        is_last = (
            last_iteration_message
            and max_iterations > 0
            and iteration == max_iterations
        )
        if is_last:
            iteration_messages = list(messages)
            iteration_messages.append(
                {"role": "system", "content": last_iteration_message}
            )
        else:
            iteration_messages = messages

        # Call LLM
        response = await llm_call(iteration_messages, tools)
        total_prompt_tokens += response.prompt_tokens
        total_completion_tokens += response.completion_tokens

        # No tool calls = done
        if not response.tool_calls:
            update_conversation(messages, response)
            yield ToolCallLoopResult(
                response_text=response.response_text or "",
                messages=messages,
                total_prompt_tokens=total_prompt_tokens,
                total_completion_tokens=total_completion_tokens,
                iterations=iteration,
                finished_naturally=True,
            )
            return

        # Execute tools — parallel or sequential depending on caller preference.
        # NOTE: asyncio.gather does not cancel sibling tasks when one raises.
        # Callers should handle errors inside execute_tool (return error
        # ToolCallResult) rather than letting exceptions propagate.
        if parallel_tool_calls and len(response.tool_calls) > 1:
            # Parallel: side-effects from different tool executors (e.g.
            # streaming events appended to a shared list) may interleave
            # nondeterministically.  Each event carries its own tool-call
            # identifier, so consumers must correlate by ID.
            tool_results: list[ToolCallResult] = list(
                await asyncio.gather(
                    *(execute_tool(tc, tools) for tc in response.tool_calls)
                )
            )
        else:
            # Sequential: preserves ordering guarantees for callers that
            # need deterministic execution order.
            tool_results = [await execute_tool(tc, tools) for tc in response.tool_calls]

        # Update conversation with response + tool results
        update_conversation(messages, response, tool_results)

        # Yield a fresh result so callers can drain buffered events
        yield ToolCallLoopResult(
            response_text="",
            messages=messages,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            iterations=iteration,
            finished_naturally=False,
            last_tool_calls=list(response.tool_calls),
        )

    # Hit max iterations
    yield ToolCallLoopResult(
        response_text=f"Completed after {max_iterations} iterations (limit reached)",
        messages=messages,
        total_prompt_tokens=total_prompt_tokens,
        total_completion_tokens=total_completion_tokens,
        iterations=iteration,
        finished_naturally=False,
    )