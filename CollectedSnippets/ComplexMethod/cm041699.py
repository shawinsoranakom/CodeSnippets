def tool_extractor(content: str) -> Union[str, list["FunctionCall"]]:
        # Extract content between tool call markers
        start_marker = "<|tool_call_start|>"
        end_marker = "<|tool_call_end|>"

        start_idx = content.find(start_marker)
        if start_idx == -1:
            return content

        end_idx = content.find(end_marker, start_idx)
        if end_idx == -1:
            return content

        tool_call_str = content[start_idx + len(start_marker) : end_idx].strip()

        # Parse Pythonic function call syntax using AST
        try:
            tree = ast.parse(tool_call_str, mode="eval")
        except SyntaxError:
            return content

        # Handle both single call and list of calls
        if isinstance(tree.body, ast.List):
            call_nodes = tree.body.elts
        elif isinstance(tree.body, ast.Call):
            call_nodes = [tree.body]
        else:
            return content

        results = []
        for node in call_nodes:
            if not isinstance(node, ast.Call):
                return content

            # Extract function name
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            else:
                return content

            # Extract keyword arguments
            args_dict = {}
            for keyword in node.keywords:
                key = keyword.arg
                try:
                    value = LFM2ToolUtils._ast_to_value(keyword.value)
                except (ValueError, SyntaxError):
                    return content
                args_dict[key] = value

            results.append(FunctionCall(func_name, json.dumps(args_dict, ensure_ascii=False)))

        return results if results else content