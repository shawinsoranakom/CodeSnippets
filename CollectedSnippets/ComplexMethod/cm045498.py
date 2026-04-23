async def run_stream(
        self,
        task: str | BaseChatMessage | Sequence[BaseChatMessage] | None,
        team_config: Union[str, Path, Dict[str, Any], ComponentModel],
        input_func: Optional[InputFuncType] = None,
        cancellation_token: Optional[CancellationToken] = None,
        env_vars: Optional[List[EnvironmentVariable]] = None,
    ) -> AsyncGenerator[Union[BaseAgentEvent | BaseChatMessage | LLMCallEvent, BaseChatMessage, TeamResult], None]:
        """Stream team execution results"""
        start_time = time.time()
        team = None

        # Setup logger correctly
        logger = logging.getLogger(EVENT_LOGGER_NAME)
        logger.setLevel(logging.INFO)
        llm_event_logger = RunEventLogger()
        logger.handlers = [llm_event_logger]  # Replace all handlers

        try:
            team = await self._create_team(team_config, input_func, env_vars)

            async for message in team.run_stream(task=task, cancellation_token=cancellation_token):
                if cancellation_token and cancellation_token.is_cancelled():
                    break

                if isinstance(message, TaskResult):
                    yield TeamResult(task_result=message, usage="", duration=time.time() - start_time)
                else:
                    yield message

                # Check for any LLM events
                while not llm_event_logger.events.empty():
                    event = await llm_event_logger.events.get()
                    yield event
        finally:
            # Cleanup - remove our handler
            if llm_event_logger in logger.handlers:
                logger.handlers.remove(llm_event_logger)

            # Ensure cleanup happens
            if team and hasattr(team, "_participants"):
                for agent in team._participants:  # type: ignore
                    if hasattr(agent, "close"):
                        await agent.close()