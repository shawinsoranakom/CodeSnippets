async def simulate_block(
    block: Any,
    input_data: dict[str, Any],
    *,
    user_id: str | None = None,
) -> AsyncGenerator[tuple[str, Any], None]:
    """Simulate block execution using an LLM.

    All block types (including MCPToolBlock) use the same generic LLM prompt
    which includes the block's run() source code for accurate simulation.

    ``user_id`` is threaded through to platform cost tracking — every dry-run
    LLM call hits the platform's OpenRouter key and is charged against the
    triggering user's rate-limit counter, same rails as copilot turns.

    Note: callers should check ``prepare_dry_run(block, input_data)`` first.
    OrchestratorBlock and AgentExecutorBlock execute for real in dry-run mode
    (see manager.py).

    Yields (output_name, output_data) tuples matching the Block.execute() interface.
    On unrecoverable failure, yields a single ("error", "[SIMULATOR ERROR ...") tuple.
    """
    # Input/output blocks are pure passthrough -- they just forward their
    # input values.  No LLM simulation needed.
    if isinstance(block, AgentInputBlock):
        value = input_data.get("value")
        if value is None:
            # Dry-run with no user input: use first dropdown option or name,
            # then coerce to a type-appropriate fallback so typed subclasses
            # (e.g. AgentNumberInputBlock → int, AgentDateInputBlock → date)
            # don't fail validation with a plain string.
            placeholder = input_data.get("options") or input_data.get(
                "placeholder_values"
            )
            if placeholder and isinstance(placeholder, list) and placeholder:
                value = placeholder[0]
            else:
                result_schema = (
                    block.output_schema.jsonschema()
                    .get("properties", {})
                    .get("result", {})
                )
                value = _default_for_input_result(
                    result_schema, input_data.get("name", "sample input")
                )
        yield "result", value
        return

    if isinstance(block, AgentOutputBlock):
        # Mirror AgentOutputBlock.run(): if a format string is provided,
        # apply Jinja2 formatting and yield only "output"; otherwise yield
        # both "output" (raw value) and "name".
        fmt = input_data.get("format", "")
        value = input_data.get("value")
        name = input_data.get("name", "")
        if fmt:
            try:
                from backend.util.text import TextFormatter  # noqa: PLC0415

                escape_html = input_data.get("escape_html", False)
                formatter = TextFormatter(autoescape=escape_html)
                formatted = await formatter.format_string(fmt, {name: value})
                yield "output", formatted
            except Exception as e:
                yield "output", f"Error: {e}, {value}"
        else:
            yield "output", value
            if name:
                yield "name", name
        return

    output_schema = block.output_schema.jsonschema()
    output_properties: dict[str, Any] = output_schema.get("properties", {})

    system_prompt, user_prompt = build_simulation_prompt(block, input_data)
    label = getattr(block, "name", "?")

    try:
        parsed = await _call_llm_for_simulation(
            system_prompt, user_prompt, label=label, user_id=user_id
        )

        # Track which pins were yielded so we can fill in missing required
        # ones afterwards — downstream nodes connected to unyielded pins
        # would otherwise stall in INCOMPLETE state.
        yielded_pins: set[str] = set()

        # Yield pins present in the LLM response with meaningful values.
        # We skip None and empty strings but preserve valid falsy values
        # like False, 0, and [].
        for pin_name in output_properties:
            if pin_name not in parsed:
                continue
            value = parsed[pin_name]
            if value is None or value == "":
                continue
            yield pin_name, value
            yielded_pins.add(pin_name)

        # For any required output pins the LLM omitted (excluding "error"),
        # yield a type-appropriate default so downstream nodes still fire.
        required_pins = set(output_schema.get("required", []))
        for pin_name in required_pins - yielded_pins - {"error"}:
            pin_schema = output_properties.get(pin_name, {})
            default = _default_for_schema(pin_schema)
            logger.debug(
                "simulate(%s): filling missing required pin %r with default %r",
                label,
                pin_name,
                default,
            )
            yield pin_name, default

    except (RuntimeError, ValueError) as e:
        yield "error", str(e)