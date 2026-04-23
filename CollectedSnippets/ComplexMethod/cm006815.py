def get_new_fields(self, inputs_vertex: list[Vertex]) -> list[dotdict]:
        new_fields: list[dotdict] = []
        vdisp_cts = Counter(v.display_name for v in inputs_vertex)

        for vertex in inputs_vertex:
            field_template = vertex.data.get("node", {}).get("template", {})
            field_order = vertex.data.get("node", {}).get("field_order", [])
            if not (field_order and field_template):
                continue
            new_vertex_inputs = [
                dotdict(
                    {
                        **field_template[input_name],
                        "name": self._get_ioput_name(vertex.id, input_name),
                        "display_name": (
                            f"{field_template[input_name]['display_name']} ({vertex.display_name})"
                            if vdisp_cts[vertex.display_name] == 1
                            else (
                                f"{field_template[input_name]['display_name']} "
                                f"({vertex.display_name}-{vertex.id.split('-')[-1]})"
                            )
                        ),
                        # TODO: make this more robust?
                        "tool_mode": not (field_template[input_name].get("advanced", False)),
                    }
                )
                for input_name in field_order
                if input_name in field_template
            ]
            new_fields.extend(new_vertex_inputs)
        return new_fields