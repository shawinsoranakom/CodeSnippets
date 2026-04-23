def build_simulation_prompt(block: Any, input_data: dict[str, Any]) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) for block simulation."""
    input_schema = block.input_schema.jsonschema()
    output_schema = block.output_schema.jsonschema()

    input_pins = _describe_schema_pins(input_schema)
    output_pins = _describe_schema_pins(output_schema)
    output_properties = list(output_schema.get("properties", {}).keys())
    # Build a separate list for the "MUST include" instruction that excludes
    # "error" — the prompt already tells the LLM to OMIT the error pin unless
    # simulating a logical error.  Including it in "MUST include" is contradictory.
    required_output_properties = [k for k in output_properties if k != "error"]

    block_name = getattr(block, "name", type(block).__name__)
    block_description = getattr(block, "description", "No description available.")

    # Include the block's run() source code so the LLM knows exactly how
    # inputs are transformed to outputs.  Truncate to avoid blowing up the
    # prompt for very large blocks.
    try:
        run_source = inspect.getsource(block.run)
        if len(run_source) > _MAX_INPUT_VALUE_CHARS:
            run_source = run_source[:_MAX_INPUT_VALUE_CHARS] + "\n# ... [TRUNCATED]"
    except (TypeError, OSError):
        run_source = ""

    implementation_section = ""
    if run_source:
        implementation_section = (
            "\n## Block Implementation (run function source code)\n"
            "```python\n"
            f"{run_source}\n"
            "```\n"
        )

    system_prompt = f"""You are simulating the execution of a software block called "{block_name}".

## Block Description
{block_description}

## Input Schema
{input_pins}

## Output Schema (what you must return)
{output_pins}
{implementation_section}
Your task: given the current inputs, produce realistic simulated outputs for this block.
{"Study the block's run() source code above to understand exactly how inputs are transformed to outputs." if run_source else "Use the block description and schemas to infer realistic outputs."}

Rules:
- Respond with a single JSON object.
- Only include output pins that have meaningful values. Omit pins with no relevant output.
- Assume all credentials and API keys are present and valid. Do not simulate auth failures.
- Generate REALISTIC, useful outputs: real-looking URLs, plausible text, valid data structures.
- Never return empty strings, null, or "N/A" for pins that should have content.
- You MAY simulate logical errors (e.g., invalid input format, unsupported operation) when the inputs warrant it — use the "error" pin for these. But do NOT simulate auth/credential errors.
- Do not include extra keys beyond the defined output pins.

Available output pins: {json.dumps(required_output_properties)}
"""

    # Strip credentials from input so the LLM doesn't see null/empty creds
    # and incorrectly simulate auth failures.  Use the block's schema to
    # detect credential fields when available, falling back to common names.
    try:
        cred_fields = set(block.input_schema.get_credentials_fields())
    except (AttributeError, TypeError):
        cred_fields = set()
    exclude_keys = cred_fields | _COMMON_CRED_KEYS
    safe_inputs = {
        k: v
        for k, v in _truncate_input_values(input_data).items()
        if k not in exclude_keys
    }
    user_prompt = f"## Current Inputs\n{json.dumps(safe_inputs, indent=2)}"

    return system_prompt, user_prompt