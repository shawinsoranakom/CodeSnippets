async def start_stream(
        self,
        run_id: int,
        task: str | ChatMessage | Sequence[ChatMessage] | None,
        team_config: str | Path | Dict[str, Any] | ComponentModel,
    ) -> None:
        """Start streaming task execution with proper run management"""
        if run_id not in self._connections or run_id in self._closed_connections:
            raise ValueError(f"No active connection for run {run_id}")
        with RunContext.populate_context(run_id=run_id):
            team_manager = TeamManager()
            cancellation_token = CancellationToken()
            self._cancellation_tokens[run_id] = cancellation_token
            final_result = None
            env_vars = None  # Ensure env_vars is always defined

            try:
                # Update run with task and status
                run = await self._get_run(run_id)

                if run is not None and run.user_id:
                    # get user Settings
                    user_settings = await self._get_settings(run.user_id)
                    env_vars = SettingsConfig(**user_settings.config).environment if user_settings else None  # type: ignore
                    run.task = self._convert_images_in_dict(MessageConfig(content=task, source="user").model_dump())
                    run.status = RunStatus.ACTIVE
                    self.db_manager.upsert(run)

                input_func = self.create_input_func(run_id)

                async for message in team_manager.run_stream(
                    task=task,
                    team_config=team_config,
                    input_func=input_func,
                    cancellation_token=cancellation_token,
                    env_vars=env_vars,
                ):
                    if cancellation_token.is_cancelled() or run_id in self._closed_connections:
                        logger.info(f"Stream cancelled or connection closed for run {run_id}")
                        break

                    formatted_message = self._format_message(message)
                    if formatted_message:
                        await self._send_message(run_id, formatted_message)

                        # Save messages by concrete type
                        if isinstance(
                            message,
                            (
                                TextMessage,
                                MultiModalMessage,
                                StopMessage,
                                HandoffMessage,
                                ToolCallRequestEvent,
                                ToolCallExecutionEvent,
                                LLMCallEventMessage,
                            ),
                        ):
                            await self._save_message(run_id, message)
                        # Capture final result if it's a TeamResult
                        elif isinstance(message, TeamResult):
                            final_result = message.model_dump()
                if not cancellation_token.is_cancelled() and run_id not in self._closed_connections:
                    if final_result:
                        await self._update_run(run_id, RunStatus.COMPLETE, team_result=final_result)
                    else:
                        logger.warning(f"No final result captured for completed run {run_id}")
                        await self._update_run_status(run_id, RunStatus.COMPLETE)
                else:
                    await self._send_message(
                        run_id,
                        {
                            "type": "completion",
                            "status": "cancelled",
                            "data": self._cancel_message,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )
                    # Update run with cancellation result
                    await self._update_run(run_id, RunStatus.STOPPED, team_result=self._cancel_message)

            except Exception as e:
                logger.error(f"Stream error for run {run_id}: {e}")
                traceback.print_exc()
                await self._handle_stream_error(run_id, e)
            finally:
                self._cancellation_tokens.pop(run_id, None)