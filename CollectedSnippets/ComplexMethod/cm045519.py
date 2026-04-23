async def chat_completions_stream(request: Request):
    json_data = await request.json()
    message = json_data.get("message", "")
    conversation_id = json_data.get("conversation_id", "conv_id")

    if not isinstance(message, str):
        raise HTTPException(status_code=400, detail="Invalid input: 'message' must be a string.")

    if not isinstance(conversation_id, str):
        raise HTTPException(status_code=400, detail="Invalid input: 'conversation_id' must be a string.")

    # Validate conversation_id to prevent path traversal attacks
    if not re.match(r'^[A-Za-z0-9_-]+$', conversation_id):
        raise HTTPException(status_code=400, detail="Invalid input: 'conversation_id' contains invalid characters.")

    chat_history_dir = "chat_history"
    base_dir = os.path.abspath(chat_history_dir)
    full_path = os.path.normpath(os.path.join(base_dir, f"history-{conversation_id}.json"))
    if not full_path.startswith(base_dir + os.sep):
        raise HTTPException(status_code=400, detail="Invalid input: 'conversation_id' leads to invalid path.")
    chat_history_file = full_path

    messages = []
    # Initialize chat_history and route_agent with default values
    chat_history = {} 
    route_agent = triage_agent_topic_type

    # Load chat history if it exists.
    # Chat history is saved inside the UserAgent. Use redis if possible.
    # There may be a better way to do this.
    if os.path.exists(chat_history_file):
        context = BufferedChatCompletionContext(buffer_size=15)
        try:
            async with aiofiles.open(chat_history_file, "r") as f:
                content = await f.read()
                if content: # Check if file is not empty
                    chat_history = json.loads(content)
                    await context.load_state(chat_history) # Load state only if history is loaded
                    loaded_messages = await context.get_messages()
                    if loaded_messages:
                        messages = loaded_messages
                        last_message = messages[-1]
                        if isinstance(last_message, AssistantMessage) and isinstance(last_message.source, str):
                            route_agent = last_message.source
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {chat_history_file}. Starting with empty history.")
            # Reset to defaults if loading fails
            messages = []
            route_agent = triage_agent_topic_type
            chat_history = {}
        except Exception as e:
            print(f"Error loading chat history for {conversation_id}: {e}")
            # Reset to defaults on other errors
            messages = []
            route_agent = triage_agent_topic_type
            chat_history = {}
    # else: route_agent remains the default triage_agent_topic_type if file doesn't exist

    messages.append(UserMessage(content=message,source="User"))



    async def response_stream() -> AsyncGenerator[str, None]:
        task1 = asyncio.create_task(runtime.publish_message(
            UserTask(context=messages),
            topic_id=TopicId(type=route_agent, source=conversation_id), # Explicitly use 'type' parameter
        ))
        # Consume items from the response queue until the stream ends or an error occurs
        while True:
            item = await response_queue.get()
            if item is STREAM_DONE:
                print(f"{time.time():.2f} - MAIN: Received STREAM_DONE. Exiting loop.")
                break
            elif isinstance(item, str) and item.startswith("ERROR:"):
                print(f"{time.time():.2f} - MAIN: Received error message from agent: {item}")
                break
            # Ensure item is serializable before yielding
            else:
                yield json.dumps({"content": item}) + "\n"

        # Wait for the task to finish.
        await task1

    return StreamingResponse(response_stream(), media_type="text/plain")