async def chat(websocket: WebSocket):
    await websocket.accept()

    # User input function used by the team.
    async def _user_input(prompt: str, cancellation_token: CancellationToken | None) -> str:
        try:
            data = await websocket.receive_json()
            message = TextMessage.model_validate(data)
            return message.content
        except WebSocketDisconnect:
            # Client disconnected while waiting for input - this is the root cause of the issue
            logger.info("Client disconnected while waiting for user input")
            raise  # Let WebSocketDisconnect propagate to be handled by outer try/except

    try:
        while True:
            # Get user message.
            data = await websocket.receive_json()
            request = TextMessage.model_validate(data)

            try:
                # Get the team and respond to the message.
                team = await get_team(_user_input)
                history = await get_history()
                stream = team.run_stream(task=request)
                async for message in stream:
                    if isinstance(message, TaskResult):
                        continue
                    await websocket.send_json(message.model_dump())
                    if not isinstance(message, UserInputRequestedEvent):
                        # Don't save user input events to history.
                        history.append(message.model_dump())

                # Save team state to file.
                async with aiofiles.open(state_path, "w") as file:
                    state = await team.save_state()
                    await file.write(json.dumps(state))

                # Save chat history to file.
                async with aiofiles.open(history_path, "w") as file:
                    await file.write(json.dumps(history))

            except WebSocketDisconnect:
                # Client disconnected during message processing - exit gracefully
                logger.info("Client disconnected during message processing")
                break
            except Exception as e:
                # Send error message to client
                error_message = {
                    "type": "error",
                    "content": f"Error: {str(e)}",
                    "source": "system"
                }
                try:
                    await websocket.send_json(error_message)
                    # Re-enable input after error
                    await websocket.send_json({
                        "type": "UserInputRequestedEvent",
                        "content": "An error occurred. Please try again.",
                        "source": "system"
                    })
                except WebSocketDisconnect:
                    # Client disconnected while sending error - exit gracefully
                    logger.info("Client disconnected while sending error message")
                    break
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {str(send_error)}")
                    break

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": f"Unexpected error: {str(e)}",
                "source": "system"
            })
        except WebSocketDisconnect:
            # Client already disconnected - no need to send
            logger.info("Client disconnected before error could be sent")
        except Exception:
            # Failed to send error message - connection likely broken
            logger.error("Failed to send error message to client")
            pass