async def chat_completion(request: ChatCompletionRequest):
        global last_start_time

        # Convert to LMC
        last_message = request.messages[-1]

        if last_message.role != "user":
            raise ValueError("Last message must be from the user.")

        if last_message.content == "{STOP}":
            # Handle special STOP token
            async_interpreter.stop_event.set()
            time.sleep(5)
            async_interpreter.stop_event.clear()
            return

        if last_message.content in ["{CONTEXT_MODE_ON}", "{REQUIRE_START_ON}"]:
            async_interpreter.context_mode = True
            return

        if last_message.content in ["{CONTEXT_MODE_OFF}", "{REQUIRE_START_OFF}"]:
            async_interpreter.context_mode = False
            return

        if last_message.content == "{AUTO_RUN_ON}":
            async_interpreter.auto_run = True
            return

        if last_message.content == "{AUTO_RUN_OFF}":
            async_interpreter.auto_run = False
            return

        run_code = False
        if (
            async_interpreter.messages
            and async_interpreter.messages[-1]["type"] == "code"
            and last_message.content.lower().strip(".!?").strip() == "yes"
        ):
            run_code = True
        elif type(last_message.content) == str:
            async_interpreter.messages.append(
                {
                    "role": "user",
                    "type": "message",
                    "content": last_message.content,
                }
            )
            print(">", last_message.content)
        elif type(last_message.content) == list:
            for content in last_message.content:
                if content["type"] == "text":
                    async_interpreter.messages.append(
                        {"role": "user", "type": "message", "content": str(content)}
                    )
                    print(">", content)
                elif content["type"] == "image_url":
                    if "url" not in content["image_url"]:
                        raise Exception("`url` must be in `image_url`.")
                    url = content["image_url"]["url"]
                    print("> [user sent an image]", url[:100])
                    if "base64," not in url:
                        raise Exception(
                            '''Image must be in the format: "data:image/jpeg;base64,{base64_image}"'''
                        )

                    # data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA6oA...

                    data = url.split("base64,")[1]
                    format = "base64." + url.split(";")[0].split("/")[1]
                    async_interpreter.messages.append(
                        {
                            "role": "user",
                            "type": "image",
                            "format": format,
                            "content": data,
                        }
                    )

        else:
            if async_interpreter.context_mode:
                # In context mode, we only respond if we received a {START} message
                # Otherwise, we're just accumulating context
                if last_message.content == "{START}":
                    if async_interpreter.messages[-1]["content"] == "{START}":
                        # Remove that {START} message that would have just been added
                        async_interpreter.messages = async_interpreter.messages[:-1]
                    last_start_time = time.time()
                    if (
                        async_interpreter.messages
                        and async_interpreter.messages[-1].get("role") != "user"
                    ):
                        return
                else:
                    # Check if we're within 6 seconds of last_start_time
                    current_time = time.time()
                    if current_time - last_start_time <= 6:
                        # Continue processing
                        pass
                    else:
                        # More than 6 seconds have passed, so return
                        return

            else:
                if last_message.content == "{START}":
                    # This just sometimes happens I guess
                    # Remove that {START} message that would have just been added
                    async_interpreter.messages = async_interpreter.messages[:-1]
                    return

        async_interpreter.stop_event.set()
        time.sleep(0.1)
        async_interpreter.stop_event.clear()

        if request.stream:
            return StreamingResponse(
                openai_compatible_generator(run_code), media_type="application/x-ndjson"
            )
        else:
            messages = async_interpreter.chat(message=".", stream=False, display=True)
            content = messages[-1]["content"]
            return {
                "id": "200",
                "object": "chat.completion",
                "created": time.time(),
                "model": request.model,
                "choices": [{"message": {"role": "assistant", "content": content}}],
            }