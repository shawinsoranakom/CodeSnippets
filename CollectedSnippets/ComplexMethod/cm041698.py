def tool_formatter(tools: list[dict[str, Any]]) -> str:
        def _format_parameters(properties: dict[str, Any]) -> str:
            parts: list[str] = []
            for name, schema in properties.items():
                item_parts: list[str] = []
                if schema.get("description"):
                    item_parts.append(f'description:<|"|>{schema["description"]}<|"|>')
                if schema.get("type"):
                    item_parts.append(f'type:<|"|>{str(schema["type"]).upper()}<|"|>')
                parts.append(f"{name}:{{{','.join(item_parts)}}}")

            return ",".join(parts)

        declarations: list[str] = []
        for tool in tools:
            function_data = tool.get("function", tool) if tool.get("type") == "function" else tool
            declaration = (
                f"declaration:{function_data['name']}"
                + "{"
                + f'description:<|"|>{function_data.get("description", "")}<|"|>'
            )

            params = function_data.get("parameters")
            if params:
                param_parts: list[str] = []
                if params.get("properties"):
                    param_parts.append(f"properties:{{{_format_parameters(params['properties'])}}}")

                if params.get("required"):
                    required_text = ",".join(f'<|"|>{item}<|"|>' for item in params["required"])
                    param_parts.append(f"required:[{required_text}]")

                if params.get("type"):
                    param_parts.append(f'type:<|"|>{str(params["type"]).upper()}<|"|>')

                declaration += f",parameters:{{{','.join(param_parts)}}}"

            response_declaration = function_data.get("response")
            if response_declaration:
                response_parts: list[str] = []
                if response_declaration.get("description"):
                    response_parts.append(f'description:<|"|>{response_declaration["description"]}<|"|>')

                response_type = str(response_declaration.get("type", "")).upper()

                if response_type == "OBJECT":
                    response_parts.append(f'type:<|"|>{response_type}<|"|>')

                declaration += f",response:{{{','.join(response_parts)}}}"

            declarations.append(declaration + "}")

        return "\n".join(declarations)