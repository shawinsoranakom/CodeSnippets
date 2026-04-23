async def openai_compatible_generator(run_code):
        if run_code:
            print("Running code.\n")
            for i, chunk in enumerate(async_interpreter._respond_and_store()):
                if "content" in chunk:
                    print(chunk["content"], end="")  # Sorry! Shitty display for now
                if "start" in chunk:
                    print("\n")

                output_content = None

                if chunk["type"] == "message" and "content" in chunk:
                    output_content = chunk["content"]
                if chunk["type"] == "code" and "start" in chunk:
                    output_content = "```" + chunk["format"] + "\n"
                if chunk["type"] == "code" and "content" in chunk:
                    output_content = chunk["content"]
                if chunk["type"] == "code" and "end" in chunk:
                    output_content = "\n```\n"

                if output_content:
                    await asyncio.sleep(0)
                    output_chunk = {
                        "id": i,
                        "object": "chat.completion.chunk",
                        "created": time.time(),
                        "model": "open-interpreter",
                        "choices": [{"delta": {"content": output_content}}],
                    }
                    yield f"data: {json.dumps(output_chunk)}\n\n"

            return

        made_chunk = False

        for message in [
            ".",
            "Just say something, anything.",
            "Hello? Answer please.",
            "Are you there?",
            "Can you respond?",
            "Please reply.",
        ]:
            for i, chunk in enumerate(
                async_interpreter.chat(message=message, stream=True, display=True)
            ):
                await asyncio.sleep(0)  # Yield control to the event loop
                made_chunk = True

                if (
                    chunk["type"] == "confirmation"
                    and async_interpreter.auto_run == False
                ):
                    await asyncio.sleep(0)
                    output_content = "Do you want to run this code?"
                    output_chunk = {
                        "id": i,
                        "object": "chat.completion.chunk",
                        "created": time.time(),
                        "model": "open-interpreter",
                        "choices": [{"delta": {"content": output_content}}],
                    }
                    yield f"data: {json.dumps(output_chunk)}\n\n"
                    break

                if async_interpreter.stop_event.is_set():
                    break

                output_content = None

                if chunk["type"] == "message" and "content" in chunk:
                    output_content = chunk["content"]
                if chunk["type"] == "code" and "start" in chunk:
                    output_content = "```" + chunk["format"] + "\n"
                if chunk["type"] == "code" and "content" in chunk:
                    output_content = chunk["content"]
                if chunk["type"] == "code" and "end" in chunk:
                    output_content = "\n```\n"

                if output_content:
                    await asyncio.sleep(0)
                    output_chunk = {
                        "id": i,
                        "object": "chat.completion.chunk",
                        "created": time.time(),
                        "model": "open-interpreter",
                        "choices": [{"delta": {"content": output_content}}],
                    }
                    yield f"data: {json.dumps(output_chunk)}\n\n"

            if made_chunk:
                break