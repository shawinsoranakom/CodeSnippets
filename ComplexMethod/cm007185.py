def process_file_field(self, field_name: str, field: dict, params: dict[str, Any]) -> dict[str, Any]:
        """Process file type fields.

        Converts logical paths (flow_id/filename) to component-ready paths.
        """
        if file_path := field.get("file_path"):
            try:
                full_path: str | list[str] = ""
                if field.get("list"):
                    full_path = []
                    if isinstance(file_path, str):
                        file_path = [file_path]
                    for p in file_path:
                        resolved = self.storage_service.resolve_component_path(p)
                        full_path.append(resolved)
                else:
                    full_path = self.storage_service.resolve_component_path(file_path)

            except ValueError as e:
                if "too many values to unpack" in str(e):
                    full_path = file_path
                else:
                    raise
            params[field_name] = full_path
        elif field.get("required"):
            field_display_name = field.get("display_name")
            logger.warning(
                "File path not found for %s in component %s. Setting to None.",
                field_display_name,
                self.vertex.display_name,
            )
            params[field_name] = None
        elif field["list"]:
            params[field_name] = []
        else:
            params[field_name] = None
        return params