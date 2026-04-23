def render_jinja_template(
    conversations: list[ChatType],
    tools: list[dict | Callable] | None = None,
    documents: ChatType | None = None,
    chat_template: str | None = None,
    return_assistant_tokens_mask: bool = False,
    continue_final_message: bool = False,
    add_generation_prompt: bool = False,
    **kwargs,
) -> str:
    if return_assistant_tokens_mask and not re.search(r"\{\%-?\s*generation\s*-?\%\}", chat_template):
        logger.warning_once(
            "return_assistant_tokens_mask==True but chat template does not contain `{% generation %}` keyword."
        )

    # Compilation function uses a cache to avoid recompiling the same template
    compiled_template = _compile_jinja_template(chat_template)

    # We accept either JSON schemas or functions for tools. If we get functions, we convert them to schemas
    if tools is not None:
        tool_schemas = []
        for tool in tools:
            if isinstance(tool, dict):
                tool_schemas.append(tool)
            elif isfunction(tool) or inspect.ismethod(tool):
                tool_schemas.append(get_json_schema(tool))
            else:
                raise ValueError(
                    "Tools should either be a JSON schema, or a callable function with type hints "
                    "and a docstring suitable for auto-conversion to a schema."
                )
    else:
        tool_schemas = None

    if documents is not None:
        for document in documents:
            if not isinstance(document, dict):
                raise TypeError("Documents should be a list of dicts with 'title' and 'text' keys!")

    rendered = []
    all_generation_indices = []
    continue_final_message_tag = "CONTINUE_FINAL_MESSAGE_TAG "
    for chat in conversations:
        if hasattr(chat, "messages"):
            # Indicates it's a Conversation object
            chat = chat.messages
        if continue_final_message:
            chat = deepcopy(chat)
            final_message = chat[-1].get("content")
            if final_message is None:
                raise ValueError("continue_final_message is set but the final message has no content to continue!")
            elif isinstance(final_message, (list, tuple)):
                for content_block in reversed(final_message):
                    if "text" in content_block:
                        # Pick the last text block in the message (the first one we hit while iterating in reverse)
                        final_message = content_block["text"]
                        content_block["text"] = content_block["text"] + continue_final_message_tag
                        break
                else:
                    raise ValueError(
                        "continue_final_message is set but we could not find any text to continue in the final message!"
                    )
            else:
                chat[-1]["content"] = chat[-1]["content"] + continue_final_message_tag
        if return_assistant_tokens_mask:
            rendered_chat, generation_indices = _render_with_assistant_indices(
                compiled_template=compiled_template,
                messages=chat,
                tools=tool_schemas,
                documents=documents,
                add_generation_prompt=add_generation_prompt,
                **kwargs,
            )
            all_generation_indices.append(generation_indices)
        else:
            rendered_chat = compiled_template.render(
                messages=chat,
                tools=tool_schemas,
                documents=documents,
                add_generation_prompt=add_generation_prompt,
                **kwargs,
            )
        if continue_final_message:
            if (final_message.strip() not in rendered_chat) or (
                continue_final_message_tag.strip() not in rendered_chat
            ):
                raise ValueError(
                    "continue_final_message is set but the final message does not appear in the chat after "
                    "applying the chat template! This can happen if the chat template deletes portions of "
                    "the final message. Please verify the chat template and final message in your chat to "
                    "ensure they are compatible."
                )
            tag_loc = rendered_chat.rindex(continue_final_message_tag.strip())
            if rendered_chat[tag_loc : tag_loc + len(continue_final_message_tag)] == continue_final_message_tag:
                # The template preserves spacing, so things are simple
                rendered_chat = rendered_chat[:tag_loc]
            else:
                # The message has trailing spacing that was trimmed, so we must be more cautious
                rendered_chat = rendered_chat[:tag_loc].rstrip()
        rendered.append(rendered_chat)

    return rendered, all_generation_indices