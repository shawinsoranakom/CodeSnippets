async def execute_tool(session):
        # Get flow id from name
        flow = await get_flow_snake_case(name, current_user.id, session, is_action=is_action)
        if not flow:
            msg = f"Flow with name '{name}' not found"
            raise ValueError(msg)

        # If project_id is provided, verify the flow belongs to the project
        if project_id and flow.folder_id != project_id:
            msg = f"Flow '{name}' not found in project {project_id}"
            raise ValueError(msg)

        # Process inputs
        processed_inputs = dict(arguments)

        # Initial progress notification
        if mcp_config.enable_progress_notifications and (progress_token := server.request_context.meta.progressToken):
            await server.request_context.session.send_progress_notification(
                progress_token=progress_token, progress=0.0, total=1.0
            )

        conversation_id = str(uuid4())
        input_request = SimplifiedAPIRequest(
            input_value=processed_inputs.get("input_value", ""), session_id=conversation_id
        )

        async def send_progress_updates(progress_token):
            try:
                progress = 0.0
                while True:
                    await server.request_context.session.send_progress_notification(
                        progress_token=progress_token, progress=min(0.9, progress), total=1.0
                    )
                    progress += 0.1
                    await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                if mcp_config.enable_progress_notifications:
                    await server.request_context.session.send_progress_notification(
                        progress_token=progress_token, progress=1.0, total=1.0
                    )
                raise

        collected_results = []
        try:
            progress_task = None
            if mcp_config.enable_progress_notifications and server.request_context.meta.progressToken:
                progress_task = asyncio.create_task(send_progress_updates(server.request_context.meta.progressToken))

            try:
                try:
                    result = await simple_run_flow(
                        flow=flow,
                        input_request=input_request,
                        stream=False,
                        api_key_user=current_user,
                        context=exec_context,
                    )
                    # Process all outputs and messages, ensuring no duplicates
                    processed_texts = set()

                    def add_result(text: str):
                        if text not in processed_texts:
                            processed_texts.add(text)
                            collected_results.append(types.TextContent(type="text", text=text))

                    for run_output in result.outputs:
                        for component_output in run_output.outputs:
                            # Handle messages
                            for msg in component_output.messages or []:
                                add_result(msg.message)
                            # Handle results
                            for value in (component_output.results or {}).values():
                                if isinstance(value, Message):
                                    add_result(value.get_text())
                                else:
                                    add_result(str(value))
                except CustomComponentValidationError as exc:
                    logger.warning(f"MCP tool call blocked for flow {flow.id}: {exc!s}")
                    collected_results.append(types.TextContent(type="text", text=f"Flow build blocked: {exc!s}"))
                except ValueError as exc:
                    error_msg = f"Error Executing the {flow.name} tool. Error: {exc!s}"
                    collected_results.append(types.TextContent(type="text", text=error_msg))
                except Exception as e:  # noqa: BLE001
                    error_msg = f"Error Executing the {flow.name} tool. Error: {e!s}"
                    collected_results.append(types.TextContent(type="text", text=error_msg))

                return collected_results
            finally:
                if progress_task:
                    progress_task.cancel()
                    await asyncio.gather(progress_task, return_exceptions=True)

        except Exception:
            if mcp_config.enable_progress_notifications and (
                progress_token := server.request_context.meta.progressToken
            ):
                await server.request_context.session.send_progress_notification(
                    progress_token=progress_token, progress=1.0, total=1.0
                )
            raise