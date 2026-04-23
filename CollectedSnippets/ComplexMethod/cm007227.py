def add_component_edge(self, source_id: str, output_input_tuple: tuple[str, str], target_id: str) -> None:
        source_vertex = self.get_vertex(source_id)
        if not isinstance(source_vertex, ComponentVertex):
            msg = f"Source vertex {source_id} is not a component vertex."
            raise TypeError(msg)
        target_vertex = self.get_vertex(target_id)
        if not isinstance(target_vertex, ComponentVertex):
            msg = f"Target vertex {target_id} is not a component vertex."
            raise TypeError(msg)
        output_name, input_name = output_input_tuple
        if source_vertex.custom_component is None:
            msg = f"Source vertex {source_id} does not have a custom component."
            raise ValueError(msg)
        if target_vertex.custom_component is None:
            msg = f"Target vertex {target_id} does not have a custom component."
            raise ValueError(msg)

        try:
            input_field = target_vertex.get_input(input_name)
            input_types = input_field.input_types
            input_field_type = str(input_field.field_type)
        except ValueError as e:
            input_field = target_vertex.data.get("node", {}).get("template", {}).get(input_name)
            if not input_field:
                msg = f"Input field {input_name} not found in target vertex {target_id}"
                raise ValueError(msg) from e
            input_types = input_field.get("input_types", [])
            input_field_type = input_field.get("type", "")

        edge_data: EdgeData = {
            "source": source_id,
            "target": target_id,
            "data": {
                "sourceHandle": {
                    "dataType": source_vertex.custom_component.name
                    or source_vertex.custom_component.__class__.__name__,
                    "id": source_vertex.id,
                    "name": output_name,
                    "output_types": source_vertex.get_output(output_name).types,
                },
                "targetHandle": {
                    "fieldName": input_name,
                    "id": target_vertex.id,
                    "inputTypes": input_types,
                    "type": input_field_type,
                },
            },
        }
        self._add_edge(edge_data)