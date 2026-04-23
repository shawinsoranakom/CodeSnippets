async def handle_function_call(
    function_call: dict,
    function_call_args: str,
    flow_id: str,
    background_tasks: BackgroundTasks,
    current_user: CurrentActiveUser,
    conversation_id: str,
    session_id: str,
    msg_handler: SendQueues,
):
    create_response = get_create_response(msg_handler, session_id)
    """Handle function calls from the OpenAI API."""
    try:
        args = json.loads(function_call_args) if function_call_args else {}
        input_request = InputValueRequest(
            input_value=args.get("input"), components=[], type="chat", session=conversation_id
        )
        response = await build_flow_and_stream(
            flow_id=UUID(flow_id),
            inputs=input_request,
            background_tasks=background_tasks,
            current_user=current_user,
        )
        result = ""
        async for line in response.body_iterator:
            if not line:
                continue
            event_data = json.loads(line)
            msg_handler.client_send({"type": "flow.build.progress", "data": event_data})
            if event_data.get("event") == "end_vertex":
                text_part = (
                    event_data.get("data", {})
                    .get("build_data", "")
                    .get("data", {})
                    .get("results", {})
                    .get("message", {})
                    .get("text", "")
                )
                result += text_part
        function_output = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": function_call.get("call_id"),
                "output": str(result),
            },
        }
        msg_handler.openai_send(function_output)
        create_response()
    except json.JSONDecodeError as e:
        trace = traceback.format_exc()
        await logger.aerror(f"JSON decode error: {e!s}\ntrace: {trace}")
        function_output = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": function_call.get("call_id"),
                "output": f"Error parsing arguments: {e!s}",
            },
        }
        msg_handler.openai_send(function_output)
    except ValueError as e:
        trace = traceback.format_exc()
        await logger.aerror(f"Value error: {e!s}\ntrace: {trace}")
        function_output = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": function_call.get("call_id"),
                "output": f"Error with input values: {e!s}",
            },
        }
        msg_handler.openai_send(function_output)
    except (ConnectionError, websockets.exceptions.WebSocketException) as e:
        trace = traceback.format_exc()
        await logger.aerror(f"Connection error: {e!s}\ntrace: {trace}")
        function_output = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": function_call.get("call_id"),
                "output": f"Connection error: {e!s}",
            },
        }
        msg_handler.openai_send(function_output)
    except (KeyError, AttributeError, TypeError) as e:
        await logger.aerror(f"Error executing flow: {e}")
        await logger.aerror(traceback.format_exc())
        function_output = {
            "type": "conversation.item.create",
            "item": {
                "type": "function_call_output",
                "call_id": function_call.get("call_id"),
                "output": f"Error executing flow: {e}",
            },
        }
        msg_handler.openai_send(function_output)