def parse_tool_calls(index: int, text: str):
    tool_calls: list[dict[str, Any]] = []
    stop_token = None
    tool_calls_end_token = f"</{dsml_token}function_calls>"

    while index < len(text):
        index, _, stop_token = _read_until_stop(
            index, text, [f"<{dsml_token}invoke", tool_calls_end_token]
        )
        if _ != ">\n":
            raise RuntimeError("Tool call format error")

        if stop_token == tool_calls_end_token:
            break

        if stop_token is None:
            raise RuntimeError("Missing special token")

        index, tool_name_content, stop_token = _read_until_stop(
            index, text, [f"<{dsml_token}parameter", f"</{dsml_token}invoke"]
        )

        p_tool_name = re.findall(
            r'^\s*name="(.*?)">\n$', tool_name_content, flags=re.DOTALL
        )
        if len(p_tool_name) != 1:
            raise RuntimeError("Tool name format error")
        tool_name = p_tool_name[0]

        tool_args: dict[str, tuple[str, str]] = {}
        while stop_token == f"<{dsml_token}parameter":
            index, param_content, stop_token = _read_until_stop(
                index, text, [f"/{dsml_token}parameter"]
            )

            param_kv = re.findall(
                r'^ name="(.*?)" string="(true|false)">(.*?)<$',
                param_content,
                flags=re.DOTALL,
            )
            if len(param_kv) != 1:
                raise RuntimeError("Parameter format error")
            param_name, string, param_value = param_kv[0]

            if param_name in tool_args:
                raise RuntimeError("Duplicate parameter name")
            tool_args[param_name] = (param_value, string)

            index, content, stop_token = _read_until_stop(
                index, text, [f"<{dsml_token}parameter", f"</{dsml_token}invoke"]
            )
            if content != ">\n":
                raise RuntimeError("Parameter format error")

        tool_call = decode_dsml_to_arguments(tool_name=tool_name, tool_args=tool_args)
        tool_calls.append(tool_call)

    return index, stop_token, tool_calls