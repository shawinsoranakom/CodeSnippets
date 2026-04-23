def update_outputs(self, frontend_node: dict[str, Any], field_name: str, field_value: Any) -> dict[str, Any]:  # noqa: ARG002
        """Dynamically show outputs based on file count/type and advanced mode."""
        if field_name not in ["path", "advanced_mode", "pipeline"]:
            return frontend_node

        template = frontend_node.get("template", {})
        paths = self._path_value(template)
        if not paths:
            return frontend_node

        frontend_node["outputs"] = []
        if len(paths) == 1:
            file_path = paths[0] if field_name == "path" else frontend_node["template"]["path"]["file_path"][0]
            if file_path.endswith((".csv", ".xlsx", ".parquet")):
                frontend_node["outputs"].append(
                    Output(
                        display_name="Structured Content",
                        name="dataframe",
                        method="load_files_structured",
                        tool_mode=True,
                    ),
                )
            elif file_path.endswith(".json"):
                frontend_node["outputs"].append(
                    Output(display_name="Structured Content", name="json", method="load_files_json", tool_mode=True),
                )

            advanced_mode = frontend_node.get("template", {}).get("advanced_mode", {}).get("value", False)
            if advanced_mode:
                frontend_node["outputs"].append(
                    Output(
                        display_name="Structured Output",
                        name="advanced_dataframe",
                        method="load_files_dataframe",
                        tool_mode=True,
                    ),
                )
                frontend_node["outputs"].append(
                    Output(
                        display_name="Markdown", name="advanced_markdown", method="load_files_markdown", tool_mode=True
                    ),
                )
                frontend_node["outputs"].append(
                    Output(display_name="File Path", name="path", method="load_files_path", tool_mode=True),
                )
            else:
                frontend_node["outputs"].append(
                    Output(display_name="Raw Content", name="message", method="load_files_message", tool_mode=True),
                )
                frontend_node["outputs"].append(
                    Output(display_name="File Path", name="path", method="load_files_path", tool_mode=True),
                )
        else:
            # Multiple files => DataFrame output; advanced parser disabled
            frontend_node["outputs"].append(
                Output(display_name="Files", name="dataframe", method="load_files", tool_mode=True)
            )

        return frontend_node