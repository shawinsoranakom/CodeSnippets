async def parse_commands(command_rsp: str, llm, exclusive_tool_commands: list[str]) -> Tuple[list[dict], bool]:
    """Retrieves commands from the Large Language Model (LLM).

    This function attempts to retrieve a list of commands from the LLM by
    processing the response (`command_rsp`). It handles potential errors
    during parsing and LLM response formats.

    Returns:
        A tuple containing:
            - A boolean flag indicating success (True) or failure (False).
    """
    try:
        commands = CodeParser.parse_code(block=None, lang="json", text=command_rsp)
        if commands.endswith("]") and not commands.startswith("["):
            commands = "[" + commands
        commands = json.loads(repair_llm_raw_output(output=commands, req_keys=[None], repair_type=RepairType.JSON))
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON for: {command_rsp}. Trying to repair...")
        commands = await llm.aask(msg=JSON_REPAIR_PROMPT.format(json_data=command_rsp, json_decode_error=str(e)))
        try:
            commands = json.loads(CodeParser.parse_code(block=None, lang="json", text=commands))
        except json.JSONDecodeError:
            # repair escape error of code and math
            commands = CodeParser.parse_code(block=None, lang="json", text=command_rsp)
            new_command = repair_escape_error(commands)
            commands = json.loads(
                repair_llm_raw_output(output=new_command, req_keys=[None], repair_type=RepairType.JSON)
            )
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        error_msg = str(e)
        return error_msg, False, command_rsp

    # 为了对LLM不按格式生成进行容错
    if isinstance(commands, dict):
        commands = commands["commands"] if "commands" in commands else [commands]

    # Set the exclusive command flag to False.
    command_flag = [command["command_name"] not in exclusive_tool_commands for command in commands]
    if command_flag.count(False) > 1:
        # Keep only the first exclusive command
        index_of_first_exclusive = command_flag.index(False)
        commands = commands[: index_of_first_exclusive + 1]
        command_rsp = "```json\n" + json.dumps(commands, indent=4, ensure_ascii=False) + "\n```"
        logger.info("exclusive command more than one in current command list. change the command list.\n" + command_rsp)
    return commands, True, command_rsp