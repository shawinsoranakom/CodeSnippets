async def test_fastapi_server():
        import asyncio

        async with websockets.connect("ws://localhost:8000/") as websocket:
            # Connect to the websocket
            print("Connected to WebSocket")

            # Sending message via WebSocket
            await websocket.send(json.dumps({"auth": "dummy-api-key"}))

            # Sending POST request
            post_url = "http://localhost:8000/settings"
            settings = {
                "llm": {"model": "gpt-4o-mini"},
                "messages": [
                    {
                        "role": "user",
                        "type": "message",
                        "content": "The secret word is 'crunk'.",
                    },
                    {"role": "assistant", "type": "message", "content": "Understood."},
                ],
                "custom_instructions": "",
                "auto_run": True,
            }
            response = requests.post(post_url, json=settings)
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
                        "content": "What's the secret word?",
                    }
                )
            )
            await websocket.send(
                json.dumps({"role": "user", "type": "message", "end": True})
            )
            print("WebSocket chunks sent")

            # Wait for a specific response
            accumulated_content = ""
            while True:
                message = await websocket.recv()
                message_data = json.loads(message)
                if "error" in message_data:
                    raise Exception(message_data["content"])
                print("Received from WebSocket:", message_data)
                if type(message_data.get("content")) == str:
                    accumulated_content += message_data.get("content")
                if message_data == {
                    "role": "server",
                    "type": "status",
                    "content": "complete",
                }:
                    print("Received expected message from server")
                    break

            assert "crunk" in accumulated_content

            # Send another POST request
            post_url = "http://localhost:8000/settings"
            settings = {
                "llm": {"model": "gpt-4o-mini"},
                "messages": [
                    {
                        "role": "user",
                        "type": "message",
                        "content": "The secret word is 'barloney'.",
                    },
                    {"role": "assistant", "type": "message", "content": "Understood."},
                ],
                "custom_instructions": "",
                "auto_run": True,
            }
            response = requests.post(post_url, json=settings)
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
                        "content": "What's the secret word?",
                    }
                )
            )
            await websocket.send(
                json.dumps({"role": "user", "type": "message", "end": True})
            )
            print("WebSocket chunks sent")

            # Wait for a specific response
            accumulated_content = ""
            while True:
                message = await websocket.recv()
                message_data = json.loads(message)
                if "error" in message_data:
                    raise Exception(message_data["content"])
                print("Received from WebSocket:", message_data)
                if message_data.get("content"):
                    accumulated_content += message_data.get("content")
                if message_data == {
                    "role": "server",
                    "type": "status",
                    "content": "complete",
                }:
                    print("Received expected message from server")
                    break

            assert "barloney" in accumulated_content

            # Send another POST request
            post_url = "http://localhost:8000/settings"
            settings = {
                "messages": [],
                "custom_instructions": "",
                "auto_run": False,
                "verbose": False,
            }
            response = requests.post(post_url, json=settings)
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
                        "content": "What's 239023*79043? Use Python.",
                    }
                )
            )
            await websocket.send(
                json.dumps({"role": "user", "type": "message", "end": True})
            )
            print("WebSocket chunks sent")

            # Wait for response
            accumulated_content = ""
            while True:
                message = await websocket.recv()
                message_data = json.loads(message)
                if "error" in message_data:
                    raise Exception(message_data["content"])
                print("Received from WebSocket:", message_data)
                if message_data.get("content"):
                    accumulated_content += message_data.get("content")
                if message_data == {
                    "role": "server",
                    "type": "status",
                    "content": "complete",
                }:
                    print("Received expected message from server")
                    break

            time.sleep(5)

            # Send a GET request to /settings/messages
            get_url = "http://localhost:8000/settings/messages"
            response = requests.get(get_url)
            print("GET request sent, response:", response.json())

            # Assert that the last message has a type of 'code'
            response_json = response.json()
            if isinstance(response_json, str):
                response_json = json.loads(response_json)
            messages = response_json["messages"] if "messages" in response_json else []
            assert messages[-1]["type"] == "code"
            assert "18893094989" not in accumulated_content.replace(",", "")

            # Send go message
            await websocket.send(
                json.dumps({"role": "user", "type": "command", "start": True})
            )
            await websocket.send(
                json.dumps(
                    {
                        "role": "user",
                        "type": "command",
                        "content": "go",
                    }
                )
            )
            await websocket.send(
                json.dumps({"role": "user", "type": "command", "end": True})
            )

            # Wait for a specific response
            accumulated_content = ""
            while True:
                message = await websocket.recv()
                message_data = json.loads(message)
                if "error" in message_data:
                    raise Exception(message_data["content"])
                print("Received from WebSocket:", message_data)
                if message_data.get("content"):
                    if type(message_data.get("content")) == str:
                        accumulated_content += message_data.get("content")
                if message_data == {
                    "role": "server",
                    "type": "status",
                    "content": "complete",
                }:
                    print("Received expected message from server")
                    break

            assert "18893094989" in accumulated_content.replace(",", "")

            #### TEST FILE ####

            # Send another POST request
            post_url = "http://localhost:8000/settings"
            settings = {"messages": [], "auto_run": True}
            response = requests.post(post_url, json=settings)
            print("POST request sent, response:", response.json())

            # Sending messages via WebSocket
            await websocket.send(json.dumps({"role": "user", "start": True}))
            print("sent", json.dumps({"role": "user", "start": True}))
            await websocket.send(
                json.dumps(
                    {
                        "role": "user",
                        "type": "message",
                        "content": "Does this file exist?",
                    }
                )
            )
            print(
                "sent",
                {
                    "role": "user",
                    "type": "message",
                    "content": "Does this file exist?",
                },
            )
            await websocket.send(
                json.dumps(
                    {
                        "role": "user",
                        "type": "file",
                        "format": "path",
                        "content": "/something.txt",
                    }
                )
            )
            print(
                "sent",
                {
                    "role": "user",
                    "type": "file",
                    "format": "path",
                    "content": "/something.txt",
                },
            )
            await websocket.send(json.dumps({"role": "user", "end": True}))
            print("WebSocket chunks sent")

            # Wait for response
            accumulated_content = ""
            while True:
                message = await websocket.recv()
                message_data = json.loads(message)
                if "error" in message_data:
                    raise Exception(message_data["content"])
                print("Received from WebSocket:", message_data)
                if type(message_data.get("content")) == str:
                    accumulated_content += message_data.get("content")
                if message_data == {
                    "role": "server",
                    "type": "status",
                    "content": "complete",
                }:
                    print("Received expected message from server")
                    break

            # Get messages
            get_url = "http://localhost:8000/settings/messages"
            response_json = requests.get(get_url).json()
            print("GET request sent, response:", response_json)
            if isinstance(response_json, str):
                response_json = json.loads(response_json)
            messages = response_json["messages"]

            response = interpreter.computer.ai.chat(
                str(messages)
                + "\n\nIn the conversation above, does the assistant think the file exists? Yes or no? Only reply with one word— 'yes' or 'no'."
            )
            assert response.strip(" \n.").lower() == "no"

            #### TEST IMAGES ####

            # Send another POST request
            post_url = "http://localhost:8000/settings"
            settings = {"messages": [], "auto_run": True}
            response = requests.post(post_url, json=settings)
            print("POST request sent, response:", response.json())

            base64png = "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAIAAADTED8xAAADMElEQVR4nOzVwQnAIBQFQYXff81RUkQCOyDj1YOPnbXWPmeTRef+/3O/OyBjzh3CD95BfqICMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMK0CMO0TAAD//2Anhf4QtqobAAAAAElFTkSuQmCC"

            # Sending messages via WebSocket
            await websocket.send(json.dumps({"role": "user", "start": True}))
            await websocket.send(
                json.dumps(
                    {
                        "role": "user",
                        "type": "message",
                        "content": "describe this image",
                    }
                )
            )
            await websocket.send(
                json.dumps(
                    {
                        "role": "user",
                        "type": "image",
                        "format": "base64.png",
                        "content": base64png,
                    }
                )
            )
            # await websocket.send(
            #     json.dumps(
            #         {
            #             "role": "user",
            #             "type": "image",
            #             "format": "path",
            #             "content": "/Users/killianlucas/Documents/GitHub/open-interpreter/screen.png",
            #         }
            #     )
            # )

            await websocket.send(json.dumps({"role": "user", "end": True}))
            print("WebSocket chunks sent")

            # Wait for response
            accumulated_content = ""
            while True:
                message = await websocket.recv()
                message_data = json.loads(message)
                if "error" in message_data:
                    raise Exception(message_data["content"])
                print("Received from WebSocket:", message_data)
                if type(message_data.get("content")) == str:
                    accumulated_content += message_data.get("content")
                if message_data == {
                    "role": "server",
                    "type": "status",
                    "content": "complete",
                }:
                    print("Received expected message from server")
                    break

            # Get messages
            get_url = "http://localhost:8000/settings/messages"
            response_json = requests.get(get_url).json()
            print("GET request sent, response:", response_json)
            if isinstance(response_json, str):
                response_json = json.loads(response_json)
            messages = response_json["messages"]

            response = interpreter.computer.ai.chat(
                str(messages)
                + "\n\nIn the conversation above, does the assistant appear to be able to describe the image of a gradient? Yes or no? Only reply with one word— 'yes' or 'no'."
            )
            assert response.strip(" \n.").lower() == "yes"

            # Sending POST request to /run endpoint with code to kill a thread in Python
            # actually wait i dont think this will work..? will just kill the python interpreter
            post_url = "http://localhost:8000/run"
            code_data = {
                "code": "import os, signal; os.kill(os.getpid(), signal.SIGINT)",
                "language": "python",
            }
            response = requests.post(post_url, json=code_data)
            print("POST request sent, response:", response.json())