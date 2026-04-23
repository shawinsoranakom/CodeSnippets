def parse_data(self) -> None:
        self.data = self.full_data["data"]
        if self.data["node"]["template"]["_type"] == "Component":
            if "outputs" not in self.data["node"]:
                msg = f"Outputs not found for {self.display_name}"
                raise ValueError(msg)
            self.outputs = self.data["node"]["outputs"]
        else:
            self.outputs = self.data["node"].get("outputs", [])
            self.output = self.data["node"]["base_classes"]

        self.display_name: str = self.data["node"].get("display_name", self.id.split("-")[0])
        self.icon: str = self.data["node"].get("icon", self.id.split("-")[0])

        self.description: str = self.data["node"].get("description", "")
        self.frozen: bool = self.data["node"].get("frozen", False)

        self.is_input = self.data["node"].get("is_input") or self.is_input
        self.is_output = self.data["node"].get("is_output") or self.is_output
        template_dicts = {key: value for key, value in self.data["node"]["template"].items() if isinstance(value, dict)}

        self.has_session_id = "session_id" in template_dicts

        self.required_inputs: list[str] = []
        self.optional_inputs: list[str] = []
        for value_dict in template_dicts.values():
            list_to_append = self.required_inputs if value_dict.get("required") else self.optional_inputs

            if "type" in value_dict:
                list_to_append.append(value_dict["type"])
            if "input_types" in value_dict:
                list_to_append.extend(value_dict["input_types"])

        template_dict = self.data["node"]["template"]
        self.vertex_type = (
            self.data["type"]
            if "Tool" not in [type_ for out in self.outputs for type_ in out["types"]]
            or template_dict["_type"].islower()
            else template_dict["_type"]
        )

        if self.base_type is None:
            for base_type, value in lazy_load_dict.all_types_dict.items():
                if self.vertex_type in value:
                    self.base_type = base_type
                    break