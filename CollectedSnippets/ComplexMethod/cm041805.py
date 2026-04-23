async def test_fastapi_server():
        import asyncio

        async with websockets.connect("ws://localhost:8000/") as websocket:
            # Connect to the websocket
            print("Connected to WebSocket")

            # Sending message via WebSocket
            await websocket.send(json.dumps({"auth": "testing"}))

            # Sending POST request
            post_url = "http://localhost:8000/settings"
            settings = {
                "llm": {
                    "model": "gpt-4o",
                    "execution_instructions": "",
                    "supports_functions": False,
                },
                "system_message": "You are a poem writing bot. Do not do anything but respond with a poem.",
                "auto_run": True,
            }
            response = requests.post(
                post_url, json=settings, headers={"X-API-KEY": "testing"}
            )
            print("POST request sent, response:", response.json())

            # Sending messages via WebSocket
            await websocket.send(
                json.dumps({"role": "user", "type": "message", "start": True})
            )
            await websocket.send(
                json.dumps(
                    {
                        "role": "user",
                        "type": "message",
                        "content": "Write a short poem about Seattle.",
                    }
                )
            )
            await websocket.send(
                json.dumps({"role": "user", "type": "message", "end": True})
            )
            print("WebSocket chunks sent")

            max_chunks = 5

            poem = ""
            while True:
                max_chunks -= 1
                if max_chunks == 0:
                    break
                message = await websocket.recv()
                message_data = json.loads(message)
                if "id" in message_data:
                    await websocket.send(json.dumps({"ack": message_data["id"]}))
                if "error" in message_data:
                    raise Exception(str(message_data))
                print("Received from WebSocket:", message_data)
                if type(message_data.get("content")) == str:
                    poem += message_data.get("content")
                    print(message_data.get("content"), end="", flush=True)
                if message_data == {
                    "role": "server",
                    "type": "status",
                    "content": "complete",
                }:
                    raise (
                        Exception(
                            "It shouldn't have finished this soon, accumulated_content is: "
                            + accumulated_content
                        )
                    )

            await websocket.close()
            print("Disconnected from WebSocket")

        time.sleep(3)

        # Now let's hilariously keep going
        print("RESUMING")

        async with websockets.connect("ws://localhost:8000/") as websocket:
            # Connect to the websocket
            print("Connected to WebSocket")

            # Sending message via WebSocket
            await websocket.send(json.dumps({"auth": "testing"}))

            while True:
                message = await websocket.recv()
                message_data = json.loads(message)
                if "id" in message_data:
                    await websocket.send(json.dumps({"ack": message_data["id"]}))
                if "error" in message_data:
                    raise Exception(str(message_data))
                print("Received from WebSocket:", message_data)
                message_data.pop("id", "")
                if message_data == {
                    "role": "server",
                    "type": "status",
                    "content": "complete",
                }:
                    break
                if type(message_data.get("content")) == str:
                    poem += message_data.get("content")
                    print(message_data.get("content"), end="", flush=True)

            time.sleep(1)
            print("Is this a normal poem?")
            print(poem)
            time.sleep(1)