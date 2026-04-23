async def receive_input():
                authenticated = False
                while True:
                    try:
                        if websocket.client_state != WebSocketState.CONNECTED:
                            return
                        data = await websocket.receive()

                        if (
                            not authenticated
                            and os.getenv("INTERPRETER_REQUIRE_AUTH") != "False"
                        ):
                            if "text" in data:
                                data = json.loads(data["text"])
                                if "auth" in data:
                                    if async_interpreter.server.authenticate(
                                        data["auth"]
                                    ):
                                        authenticated = True
                                        await websocket.send_text(
                                            json.dumps({"auth": True})
                                        )
                            if not authenticated:
                                await websocket.send_text(json.dumps({"auth": False}))
                            continue

                        if data.get("type") == "websocket.receive":
                            if "text" in data:
                                data = json.loads(data["text"])
                                if (
                                    async_interpreter.require_acknowledge
                                    and "ack" in data
                                ):
                                    async_interpreter.acknowledged_outputs.append(
                                        data["ack"]
                                    )
                                    continue
                            elif "bytes" in data:
                                data = data["bytes"]
                            await async_interpreter.input(data)
                        elif data.get("type") == "websocket.disconnect":
                            print("Client wants to disconnect, that's fine..")
                            return
                        else:
                            print("Invalid data:", data)
                            continue

                    except Exception as e:
                        error = traceback.format_exc() + "\n" + str(e)
                        error_message = {
                            "role": "server",
                            "type": "error",
                            "content": traceback.format_exc() + "\n" + str(e),
                        }
                        if websocket.client_state == WebSocketState.CONNECTED:
                            await websocket.send_text(json.dumps(error_message))
                            await websocket.send_text(json.dumps(complete_message))
                            print("\n\n--- SENT ERROR: ---\n\n")
                        else:
                            print(
                                "\n\n--- ERROR (not sent due to disconnected state): ---\n\n"
                            )
                        print(error)
                        print("\n\n--- (ERROR ABOVE) ---\n\n")