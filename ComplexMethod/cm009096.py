def _construct_lc_result_from_responses_api(
    response: Response,
    schema: type[_BM] | None = None,
    metadata: dict | None = None,
    output_version: str | None = None,
) -> ChatResult:
    """Construct `ChatResponse` from OpenAI Response API response."""
    if response.error:
        raise ValueError(response.error)

    if output_version is None:
        # Sentinel value of None lets us know if output_version is set explicitly.
        # Explicitly setting `output_version="responses/v1"` separately enables the
        # Responses API.
        output_version = "responses/v1"

    response_metadata = {
        k: v
        for k, v in response.model_dump(exclude_none=True, mode="json").items()
        if k
        in (
            "created_at",
            # backwards compatibility: keep response ID in response_metadata as well as
            # top-level-id
            "id",
            "incomplete_details",
            "metadata",
            "object",
            "status",
            "user",
            "model",
            "service_tier",
        )
    }
    if metadata:
        response_metadata.update(metadata)
    # for compatibility with chat completion calls.
    response_metadata["model_provider"] = "openai"
    response_metadata["model_name"] = response_metadata.get("model")
    if response.usage:
        usage_metadata = _create_usage_metadata_responses(
            response.usage.model_dump(), response.service_tier
        )
    else:
        usage_metadata = None

    content_blocks: list = []
    tool_calls = []
    invalid_tool_calls = []
    additional_kwargs: dict = {}
    for output in response.output:
        if output.type == "message":
            phase = getattr(output, "phase", None)
            for content in output.content:
                if content.type == "output_text":
                    block = {
                        "type": "text",
                        "text": content.text,
                        "annotations": [
                            _format_annotation_to_lc(annotation.model_dump())
                            for annotation in content.annotations
                        ]
                        if isinstance(content.annotations, list)
                        else [],
                        "id": output.id,
                    }
                    if phase is not None:
                        block["phase"] = phase
                    content_blocks.append(block)
                    if hasattr(content, "parsed"):
                        additional_kwargs["parsed"] = content.parsed
                if content.type == "refusal":
                    refusal_block = {
                        "type": "refusal",
                        "refusal": content.refusal,
                        "id": output.id,
                    }
                    if phase is not None:
                        refusal_block["phase"] = phase
                    content_blocks.append(refusal_block)
        elif output.type == "function_call":
            content_blocks.append(output.model_dump(exclude_none=True, mode="json"))
            try:
                args = json.loads(output.arguments, strict=False)
                error = None
            except JSONDecodeError as e:
                args = output.arguments
                error = str(e)
            if error is None:
                tool_call = {
                    "type": "tool_call",
                    "name": output.name,
                    "args": args,
                    "id": output.call_id,
                }
                tool_calls.append(tool_call)
            else:
                tool_call = {
                    "type": "invalid_tool_call",
                    "name": output.name,
                    "args": args,
                    "id": output.call_id,
                    "error": error,
                }
                invalid_tool_calls.append(tool_call)
        elif output.type == "custom_tool_call":
            content_blocks.append(output.model_dump(exclude_none=True, mode="json"))
            tool_call = {
                "type": "tool_call",
                "name": output.name,
                "args": {"__arg1": output.input},
                "id": output.call_id,
            }
            tool_calls.append(tool_call)
        elif output.type in (
            "reasoning",
            "compaction",
            "web_search_call",
            "file_search_call",
            "computer_call",
            "code_interpreter_call",
            "mcp_call",
            "mcp_list_tools",
            "mcp_approval_request",
            "image_generation_call",
            "tool_search_call",
            "tool_search_output",
        ):
            content_blocks.append(output.model_dump(exclude_none=True, mode="json"))

    # Workaround for parsing structured output in the streaming case.
    #    from openai import OpenAI
    #    from pydantic import BaseModel

    #    class Foo(BaseModel):
    #        response: str

    #    client = OpenAI()

    #    client.responses.parse(
    #        model="...",
    #        input=[{"content": "how are ya", "role": "user"}],
    #        text_format=Foo,
    #        stream=True,  # <-- errors
    #    )
    output_text = _get_output_text(response)
    if (
        schema is not None
        and "parsed" not in additional_kwargs
        and output_text  # tool calls can generate empty output text
        and response.text
        and (text_config := response.text.model_dump())
        and (format_ := text_config.get("format", {}))
        and (format_.get("type") == "json_schema")
    ):
        try:
            parsed_dict = json.loads(output_text)
            if schema and _is_pydantic_class(schema):
                parsed = schema(**parsed_dict)
            else:
                parsed = parsed_dict
            additional_kwargs["parsed"] = parsed
        except json.JSONDecodeError:
            pass

    message = AIMessage(
        content=content_blocks,
        id=response.id,
        usage_metadata=usage_metadata,
        response_metadata=response_metadata,
        additional_kwargs=additional_kwargs,
        tool_calls=tool_calls,
        invalid_tool_calls=invalid_tool_calls,
    )
    if output_version == "v0":
        message = _convert_to_v03_ai_message(message)

    return ChatResult(generations=[ChatGeneration(message=message)])