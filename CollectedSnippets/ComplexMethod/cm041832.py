async def send_message(output):
                if isinstance(output, dict) and "id" in output:
                    id = output["id"]
                else:
                    id = shortuuid.uuid()
                    if (
                        isinstance(output, dict)
                        and async_interpreter.require_acknowledge
                    ):
                        output["id"] = id

                for attempt in range(20):
                    # time.sleep(0.5)

                    if websocket.client_state != WebSocketState.CONNECTED:
                        return False

                    try:
                        # print("sending:", output)

                        if isinstance(output, bytes):
                            await websocket.send_bytes(output)
                            return True  # Haven't set up ack for this
                        else:
                            if async_interpreter.require_acknowledge:
                                output["id"] = id
                            if async_interpreter.debug:
                                print("Sending this over the websocket:", output)
                            await websocket.send_text(json.dumps(output))

                        if async_interpreter.require_acknowledge:
                            acknowledged = False
                            for _ in range(100):
                                if id in async_interpreter.acknowledged_outputs:
                                    async_interpreter.acknowledged_outputs.remove(id)
                                    acknowledged = True
                                    if async_interpreter.debug:
                                        print("This output was acknowledged:", output)
                                    break
                                await asyncio.sleep(0.0001)

                            if acknowledged:
                                return True
                            else:
                                if async_interpreter.debug:
                                    print("Acknowledgement not received for:", output)
                                return False
                        else:
                            return True

                    except Exception as e:
                        print(
                            f"Failed to send output on attempt number: {attempt + 1}. Output was: {output}"
                        )
                        print(f"Error: {str(e)}")
                        traceback.print_exc()
                        await asyncio.sleep(0.01)

                # If we've reached this point, we've failed to send after 100 attempts
                if output not in async_interpreter.unsent_messages:
                    print("Failed to send message:", output)
                else:
                    print(
                        "Failed to send message, also it was already in unsent queue???:",
                        output,
                    )

                return False