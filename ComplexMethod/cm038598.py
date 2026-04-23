def get_system_message(
    model_identity: str | None = None,
    reasoning_effort: Literal["high", "medium", "low"] | None = None,
    start_date: str | None = None,
    browser_description: str | None = None,
    python_description: str | None = None,
    container_description: str | None = None,
    instructions: str | None = None,
    with_custom_tools: bool = False,
) -> Message:
    sys_msg_content = SystemContent.new()
    if model_identity is not None:
        sys_msg_content = sys_msg_content.with_model_identity(model_identity)
    if instructions is not None and envs.VLLM_GPT_OSS_HARMONY_SYSTEM_INSTRUCTIONS:
        current_identity = sys_msg_content.model_identity
        new_identity = (
            f"{current_identity}\n{instructions}" if current_identity else instructions
        )
        sys_msg_content = sys_msg_content.with_model_identity(new_identity)
    if reasoning_effort is not None:
        sys_msg_content = sys_msg_content.with_reasoning_effort(
            REASONING_EFFORT[reasoning_effort]
        )
    if start_date is None:
        # NOTE(woosuk): This brings non-determinism in vLLM.
        # Set VLLM_SYSTEM_START_DATE to pin it.
        start_date = envs.VLLM_SYSTEM_START_DATE or datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )
    sys_msg_content = sys_msg_content.with_conversation_start_date(start_date)
    if browser_description is not None:
        sys_msg_content = sys_msg_content.with_tools(browser_description)
    if python_description is not None:
        sys_msg_content = sys_msg_content.with_tools(python_description)
    if container_description is not None:
        sys_msg_content = sys_msg_content.with_tools(container_description)
    sys_msg = Message.from_role_and_content(Role.SYSTEM, sys_msg_content)
    return sys_msg