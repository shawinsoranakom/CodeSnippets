def customize_components(
        route: HTTPRoute,
        component: OpenAPITool | OpenAPIResource | OpenAPIResourceTemplate,
    ) -> None:
        """Apply naming, tags, enable/disable, and resource mime type using per-route config."""
        # Map back to FastAPI route to read openapi_extra
        fa_route = route_lookup.get((route.path, route.method.upper()))
        mcp_cfg = _get_mcp_config_from_route(fa_route)

        if (exc := is_valid_mcp_config(mcp_cfg)) and isinstance(exc, Exception):
            logger.error(
                "Invalid MCP config found in route, '%s %s'."
                + " Skipping tool customization because of validation error ->\n%s",
                route.method,
                route.path,
                exc,
            )
            mcp_cfg = {}

        # Use the exact API prefix to determine category/subcategory/tool
        local_path = _strip_api_prefix(route.path, api_prefix)
        segments = [seg for seg in local_path.split("/") if seg and "{" not in seg]

        if segments:
            category = segments[0]
            if len(segments) == 1:
                subcategory = "general"
                tool = segments[0]
            elif len(segments) == 2:
                subcategory = "general"
                tool = segments[1]
            else:
                subcategory = segments[1]
                tool = "_".join(segments[2:])
        else:
            category, subcategory, tool = "general", "general", "root"

        # Name override
        if name := mcp_cfg.get("name"):
            component.name = name
        else:
            component.name = (
                f"{category}_{subcategory}_{tool}"
                if subcategory != "general"
                else f"{category}_{tool}"
            )

        # Tags
        component.tags.add(category)
        extra_tags = mcp_cfg.get("tags") or []
        for t in extra_tags:
            component.tags.add(str(t))

        # Compress schemas (only for OpenAPITool which has these attributes)
        if isinstance(component, OpenAPITool):
            if component.parameters:
                component.parameters = compress_schema(component.parameters)
            if hasattr(component, "output_schema"):
                output_schema = getattr(component, "output_schema", None)
                if output_schema is not None:
                    component.output_schema = compress_schema(output_schema)

        # Description trimming
        describe_override = mcp_cfg.get("describe_responses")
        if describe_override is False or (
            describe_override is None and not settings.describe_responses
        ):
            component.description = _extract_brief_description(
                component.description or ""
            )

        # Add prompt metadata to the tool description
        if isinstance(component, OpenAPITool):
            prompts = tool_prompts_map.get(component.name)
            if prompts:
                prompt_metadata_str = "\n\n**Associated Prompts:**"
                for p in prompts:
                    prompt_metadata_str += f"\n- **{p['name']}**: {p['description']}"
                    if p["arguments"]:
                        prompt_metadata_str += "\n  - Arguments: " + ", ".join(
                            [f"`{arg['name']}`" for arg in p["arguments"]]
                        )
                component.description = (
                    component.description or ""
                ) + prompt_metadata_str

        # Enable/disable: per-route override first, then category defaults
        enable_override = mcp_cfg.get("enable")
        if isinstance(enable_override, bool):
            should_enable = enable_override
        elif "all" in settings.default_tool_categories or any(
            tag in settings.default_tool_categories
            for tag in getattr(component, "tags", set())
        ):
            should_enable = True
        else:
            should_enable = False

        if should_enable and isinstance(component, OpenAPITool):
            _enabled_tools.add(component.name)

        # Resource-specific mime type
        if isinstance(component, OpenAPIResource):
            mime_type = mcp_cfg.get("mime_type")
            if isinstance(mime_type, str) and mime_type:
                component.mime_type = mime_type

        # Register tool in the category index for discovery browsing
        if isinstance(component, OpenAPITool):
            category_index.register(
                category=category,
                subcategory=subcategory,
                tool_name=component.name,
                description=component.description or "",
            )