async def send_output():
                while True:
                    if websocket.client_state != WebSocketState.CONNECTED:
                        return
                    try:
                        # First, try to send any unsent messages
                        while async_interpreter.unsent_messages:
                            output = async_interpreter.unsent_messages[0]
                            if async_interpreter.debug:
                                print("This was unsent, sending it again:", output)

                            success = await send_message(output)
                            if success:
                                async_interpreter.unsent_messages.popleft()

                        # If we've sent all unsent messages, get a new output
                        if not async_interpreter.unsent_messages:
                            output = await async_interpreter.output()
                            success = await send_message(output)
                            if not success:
                                async_interpreter.unsent_messages.append(output)
                                if async_interpreter.debug:
                                    print(
                                        f"Added message to unsent_messages queue after failed attempts: {output}"
                                    )

                    except Exception as e:
                        error = traceback.format_exc() + "\n" + str(e)
                        error_message = {
                            "role": "server",
                            "type": "error",
                            "content": error,
                        }
                        async_interpreter.unsent_messages.append(error_message)
                        async_interpreter.unsent_messages.append(complete_message)
                        print("\n\n--- ERROR (will be sent when possible): ---\n\n")
                        print(error)
                        print(
                            "\n\n--- (ERROR ABOVE WILL BE SENT WHEN POSSIBLE) ---\n\n"
                        )