def _cast_arguments(
        self,
        func_name: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        for tool in self.tools or []:
            if tool.function.name == func_name:
                schema = tool.function.parameters or {}
                properties = schema.get("properties", {})
                for key, value in params.items():
                    if not isinstance(value, str):
                        continue
                    prop = properties.get(key, {})
                    typ = prop.get("type")
                    if typ == "string":
                        params[key] = value.strip()
                    elif typ == "integer":
                        with contextlib.suppress(ValueError):
                            params[key] = int(value)
                    elif typ == "number":
                        with contextlib.suppress(ValueError):
                            params[key] = float(value)
                    elif typ == "boolean":
                        lower_val = value.lower()
                        params[key] = (
                            lower_val == "true"
                            if lower_val in ("true", "false")
                            else value
                        )
                    elif typ == "null":
                        params[key] = None if value.lower() == "null" else value
                break
        return params