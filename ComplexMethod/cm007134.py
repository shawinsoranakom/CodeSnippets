async def update_build_config(
        self, build_config: dotdict, field_value: Any, field_name: str | None = None
    ) -> dotdict:
        if field_name is None:
            return build_config

        if field_name not in {"tool_code", "tool_function"}:
            return build_config

        try:
            named_functions = {}
            [classes, functions] = self._parse_code(build_config["tool_code"]["value"])
            existing_fields = {}
            if len(build_config) > len(self.DEFAULT_KEYS):
                for key in build_config.copy():
                    if key not in self.DEFAULT_KEYS:
                        existing_fields[key] = build_config.pop(key)

            names = []
            for func in functions:
                named_functions[func["name"]] = func
                names.append(func["name"])

                for arg in func["args"]:
                    field_name = f"{func['name']}|{arg['name']}"
                    if field_name in existing_fields:
                        build_config[field_name] = existing_fields[field_name]
                        continue

                    field = MessageTextInput(
                        display_name=f"{arg['name']}: Description",
                        name=field_name,
                        info=f"Enter the description for {arg['name']}",
                        required=True,
                    )
                    build_config[field_name] = field.to_dict()
            build_config["_functions"]["value"] = json.dumps(named_functions)
            build_config["_classes"]["value"] = json.dumps(classes)
            build_config["tool_function"]["options"] = names
        except Exception as e:  # noqa: BLE001
            self.status = f"Failed to extract names: {e}"
            logger.debug(self.status, exc_info=True)
            build_config["tool_function"]["options"] = ["Failed to parse", str(e)]
        return build_config