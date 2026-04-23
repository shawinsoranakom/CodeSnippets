async def main():
    global exit_flag
    messages: List[BetaMessageParam] = []
    model = PROVIDER_TO_DEFAULT_MODEL_NAME[APIProvider.ANTHROPIC]
    provider = APIProvider.ANTHROPIC
    system_prompt_suffix = ""

    # Check if running in server mode
    if "--server" in sys.argv:
        app = FastAPI()

        # Start the mouse position checking thread when in server mode
        mouse_thread = threading.Thread(target=check_mouse_position)
        mouse_thread.daemon = True
        mouse_thread.start()

        # Get API key from environment variable
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable must be set when running in server mode"
            )

        @app.post("/openai/chat/completions")
        async def chat_completion(request: ChatCompletionRequest):
            print("BRAND NEW REQUEST")
            # Check exit flag before processing request
            if exit_flag:
                return {"error": "Server shutting down due to mouse in corner"}

            async def stream_response():
                print("is this even happening")

                # Instead of creating converted_messages, append the last message to global messages
                global messages
                messages.append(
                    {
                        "role": request.messages[-1].role,
                        "content": [
                            {"type": "text", "text": request.messages[-1].content}
                        ],
                    }
                )

                response_chunks = []

                async def output_callback(content_block: BetaContentBlock):
                    chunk = f"data: {json.dumps({'choices': [{'delta': {'content': content_block.text}}]})}\n\n"
                    response_chunks.append(chunk)
                    yield chunk

                async def tool_output_callback(result: ToolResult, tool_id: str):
                    if result.output or result.error:
                        content = result.output if result.output else result.error
                        chunk = f"data: {json.dumps({'choices': [{'delta': {'content': content}}]})}\n\n"
                        response_chunks.append(chunk)
                        yield chunk

                try:
                    yield f"data: {json.dumps({'choices': [{'delta': {'role': 'assistant'}}]})}\n\n"

                    messages = [m for m in messages if m["content"]]
                    print(str(messages)[-100:])
                    await asyncio.sleep(4)

                    async for chunk in sampling_loop(
                        model=model,
                        provider=provider,
                        system_prompt_suffix=system_prompt_suffix,
                        messages=messages,  # Now using global messages
                        output_callback=output_callback,
                        tool_output_callback=tool_output_callback,
                        api_key=api_key,
                    ):
                        if chunk["type"] == "chunk":
                            await asyncio.sleep(0)
                            yield f"data: {json.dumps({'choices': [{'delta': {'content': chunk['chunk']}}]})}\n\n"
                        if chunk["type"] == "messages":
                            messages = chunk["messages"]

                    yield f"data: {json.dumps({'choices': [{'delta': {'content': '', 'finish_reason': 'stop'}}]})}\n\n"

                except Exception as e:
                    print("Error: An exception occurred.")
                    print(traceback.format_exc())
                    pass
                    # raise
                    # print(f"Error: {e}")
                    # yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return StreamingResponse(stream_response(), media_type="text/event-stream")

        # Instead of running uvicorn here, we'll return the app
        return app

    # Original CLI code continues here...
    print()
    print_markdown("Welcome to **Open Interpreter**.\n")
    print_markdown("---")
    time.sleep(0.5)

    # Check for API key in environment variable
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = input(
            "\nAn Anthropic API is required for OS mode.\n\nEnter your Anthropic API key: "
        )
        print_markdown("\n---")
        time.sleep(0.5)

    import random

    tips = [
        # "You can type `i` in your terminal to use Open Interpreter.",
        "**Tip:** Type `wtf` in your terminal to have Open Interpreter fix the last error.",
        # "You can type prompts after `i` in your terminal, for example, `i want you to install node`. (Yes, really.)",
        "We recommend using our desktop app for the best experience. Type `d` for early access.",
        "**Tip:** Reduce display resolution for better performance.",
    ]

    random_tip = random.choice(tips)

    markdown_text = f"""> Model set to `Claude 3.5 Sonnet (New)`, OS control enabled

{random_tip}

**Warning:** This AI has full system access and can modify files, install software, and execute commands. By continuing, you accept all risks and responsibility.

Move your mouse to any corner of the screen to exit.
"""

    print_markdown(markdown_text)

    # Start the mouse position checking thread
    mouse_thread = threading.Thread(target=check_mouse_position)
    mouse_thread.daemon = True
    mouse_thread.start()

    while not exit_flag:
        user_input = input("> ")
        print()
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        elif user_input.lower() in ["d"]:
            print_markdown(
                "---\nTo get early access to the **Open Interpreter Desktop App**, please provide the following information:\n"
            )
            first_name = input("What's your first name? ").strip()
            email = input("What's your email? ").strip()

            url = "https://neyguovvcjxfzhqpkicj.supabase.co/functions/v1/addEmailToWaitlist"
            data = {"first_name": first_name, "email": email}

            try:
                response = requests.post(url, json=data)
            except requests.RequestException as e:
                pass

            print_markdown("\nWe'll email you shortly. ✓\n---\n")
            continue

        messages.append(
            {"role": "user", "content": [{"type": "text", "text": user_input}]}
        )

        def output_callback(content_block: BetaContentBlock):
            pass

        def tool_output_callback(result: ToolResult, tool_id: str):
            if result.output:
                print(f"---\n{result.output}\n---")
            if result.error:
                print(f"---\n{result.error}\n---")

        try:
            async for chunk in sampling_loop(
                model=model,
                provider=provider,
                system_prompt_suffix=system_prompt_suffix,
                messages=messages,
                output_callback=output_callback,
                tool_output_callback=tool_output_callback,
                api_key=api_key,
            ):
                if chunk["type"] == "messages":
                    messages = chunk["messages"]
        except Exception as e:
            raise