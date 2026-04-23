def create_mcp_server(
    settings: MCPSettings,
    fastapi_app: FastAPI,
    httpx_kwargs: dict | None = None,
    auth: Any | None = None,
) -> FastMCP:
    """Create and configure the FastMCP server from a FastAPI app instance.

    Parameters
    ----------
    settings: MCPSettings
        The MCPSettings instance containing configuration options for the server.
    fastapi_app: FastAPI
        The FastAPI app instance to be used for the server.
    httpx_kwargs: dict | None
        Optional keyword arguments to pass to the httpx client.
    auth: Any | None
        The authentication provider to use for the server.
        Should be a valid FastMCP.server.auth.AuthProvider instance,
        or an object accepted by the `auth` parameter of FastMCP initialization.

    Returns
    -------
    FastMCP
        The configured FastMCP server instance.
    """
    auth_provider = None
    if auth and isinstance(auth, list | tuple) and len(auth) == 2 and all(auth):
        # pylint: disable=import-outside-toplevel
        from .auth import get_auth_provider

        auth_provider = get_auth_provider(settings)

    category_index = CategoryIndex()
    _enabled_tools: set[str] = set()

    # Single-pass processing: filter routes, build route maps, and create lookup dictionary
    processed_data = process_fastapi_routes_for_mcp(fastapi_app, settings)

    route_lookup = processed_data.route_lookup
    api_prefix = get_api_prefix(settings)
    tool_prompts_map: dict = {}

    for prompt_def in processed_data.prompt_definitions:
        tool_name = prompt_def.get("tool")

        if tool_name:
            if tool_name not in tool_prompts_map:
                tool_prompts_map[tool_name] = []
            tool_prompts_map[tool_name].append(
                {
                    "name": prompt_def.get("name"),
                    "description": prompt_def.get("description"),
                    "arguments": prompt_def.get("arguments", []),
                }
            )

    # pylint: disable=R0912
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

    # Extract httpx_client_kwargs from settings/kwargs if available
    httpx_client_kwargs = httpx_kwargs or settings.get_httpx_kwargs()

    # Get only FastMCP constructor parameters (excludes uvicorn_config, httpx_client_kwargs)
    fastmcp_kwargs = settings.get_fastmcp_kwargs()

    # Create MCP server from the processed FastAPI app.
    mcp = FastMCP.from_fastapi(
        app=fastapi_app,  # app has been modified in-place
        mcp_component_fn=customize_components,
        route_maps=processed_data.route_maps,
        httpx_client_kwargs=httpx_client_kwargs,
        auth=auth_provider,
        **fastmcp_kwargs,
    )

    # Disable ALL non-admin tools first, then selectively re-enable.
    all_registered = category_index.all_tool_names()
    if all_registered:
        mcp.disable(names=all_registered)

    if settings.enable_tool_discovery:
        # Discovery mode: everything stays disabled.
        # Agents progressively activate what they need per-session
        # via activate_tools / activate_category.
        pass
    elif _enabled_tools:
        # Fixed-toolset mode: re-enable tools that matched
        # per-route overrides or default_tool_categories.
        mcp.enable(names=_enabled_tools)

    # Add system prompt if configured
    if settings.system_prompt_file:
        _setup_file_system_prompt(mcp, settings)

    # Load the prompts json file, if added to the settings configuration.
    _add_prompts_from_json(mcp, settings)

    # Add inline prompts from route configurations
    _add_inline_prompts(mcp, processed_data.prompt_definitions)

    # Load bundled skills via SkillsDirectoryProvider
    _bundled_skills_loaded = False
    if settings.default_skills_dir:
        skills_dir = Path(settings.default_skills_dir)
        if skills_dir.is_dir():
            mcp.add_provider(
                SkillsDirectoryProvider(
                    roots=skills_dir,
                    reload=settings.skills_reload,
                )
            )
            _bundled_skills_loaded = True
            logger.info("Loaded bundled skills from '%s'", skills_dir)

    # Load user-configured vendor skill providers
    if settings.skills_providers:
        for provider_name in settings.skills_providers:
            key = provider_name.lower().strip()
            provider_cls = _VENDOR_SKILLS_PROVIDERS.get(key)
            if provider_cls:
                mcp.add_provider(provider_cls(reload=settings.skills_reload))
                logger.info("Loaded vendor skills provider: '%s'", key)
            else:
                logger.warning(
                    "Unknown skills provider '%s'. Supported: %s",
                    key,
                    ", ".join(_VENDOR_SKILLS_PROVIDERS),
                )

    # If any skills were loaded and no custom system prompt is configured,
    # add a brief default system prompt nudging agents to discover them.
    _skills_loaded = _bundled_skills_loaded or bool(settings.skills_providers)
    if _skills_loaded and not settings.system_prompt_file:
        _add_skills_default_prompt(mcp)

    # Admin/discovery tools if enabled
    if settings.enable_tool_discovery:

        @mcp.tool(tags={"admin"})
        def available_categories() -> list[CategoryInfo]:
            """List available tool categories and subcategories with tool counts."""
            categories = category_index.get_categories()
            return [
                CategoryInfo(
                    name=category_name,
                    subcategories=[
                        SubcategoryInfo(name=subcat_name, tool_count=len(tool_names))
                        for subcat_name, tool_names in sorted(subcategories.items())
                    ],
                    total_tools=sum(
                        len(tool_names) for tool_names in subcategories.values()
                    ),
                )
                for category_name, subcategories in sorted(categories.items())
            ]

        @mcp.tool(tags={"admin"})
        async def available_tools(
            category: Annotated[
                str, Field(description="The category of tools to list")
            ],
            subcategory: Annotated[
                str | None,
                Field(
                    description="Optional subcategory to filter by. "
                    "Use 'general' for tools directly under the category."
                ),
            ] = None,
        ) -> list[ToolInfo]:
            """List tools in a specific category and subcategory."""
            cat_data = category_index.get_subcategories(category)

            if cat_data is None:
                available = list(category_index.get_categories().keys())
                raise ValueError(
                    f"Category '{category}' not found. "
                    f"Available categories: {', '.join(sorted(available))}"
                )

            if subcategory:
                names = category_index.get_subcategory_names(category, subcategory)
                if not names:
                    raise ValueError(
                        f"Subcategory '{subcategory}' not found in category '{category}'. "
                        f"Available subcategories: {', '.join(sorted(cat_data.keys()))}"
                    )
            else:
                names = category_index.get_category_names(category)

            # Resolve active state from FastMCP's live tool list
            active_tools = await mcp.list_tools()
            active_names = {t.name for t in active_tools}

            # Build descriptions — use live tool object when available,
            # fall back to cached short description from the index.
            tool_map = {t.name: t for t in active_tools}
            results: list[ToolInfo] = []
            for name in sorted(names):
                if name in tool_map:
                    desc = _extract_brief_description(tool_map[name].description or "")
                else:
                    desc = category_index.get_description(name)
                results.append(
                    ToolInfo(name=name, active=name in active_names, description=desc)
                )
            return results

        @mcp.tool(tags={"admin"})
        async def activate_tools(
            tool_names: Annotated[
                list[str], Field(description="Names of tools to activate")
            ],
            ctx: Context,
        ) -> str:
            """Activate one or more tools for this session."""
            valid = [n for n in tool_names if category_index.has_tool(n)]
            invalid = [n for n in tool_names if not category_index.has_tool(n)]
            if valid:
                await ctx.enable_components(names=set(valid))
            parts: list[str] = []
            if valid:
                parts.append(f"Activated: {', '.join(valid)}")
            if invalid:
                parts.append(f"Not found: {', '.join(invalid)}")
            return " ".join(parts) or "No tools processed."

        @mcp.tool(tags={"admin"})
        async def deactivate_tools(
            tool_names: Annotated[
                list[str], Field(description="Names of tools to deactivate")
            ],
            ctx: Context,
        ) -> str:
            """Deactivate one or more tools for this session."""
            valid = [n for n in tool_names if category_index.has_tool(n)]
            invalid = [n for n in tool_names if not category_index.has_tool(n)]
            if valid:
                await ctx.disable_components(names=set(valid))
            parts: list[str] = []
            if valid:
                parts.append(f"Deactivated: {', '.join(valid)}")
            if invalid:
                parts.append(f"Not found: {', '.join(invalid)}")
            return " ".join(parts) or "No tools processed."

        @mcp.tool(tags={"admin"})
        async def activate_category(
            category: Annotated[
                str, Field(description="Category name to activate all tools for")
            ],
            ctx: Context,
            subcategory: Annotated[
                str | None,
                Field(description="Optional subcategory to narrow activation"),
            ] = None,
        ) -> str:
            """Activate all tools in a category (or subcategory) for this session."""
            if subcategory:
                names = category_index.get_subcategory_names(category, subcategory)
            else:
                names = category_index.get_category_names(category)
            if not names:
                available = list(category_index.get_categories().keys())
                raise ValueError(
                    f"No tools found in '{category}'"
                    + (f"/'{subcategory}'" if subcategory else "")
                    + f". Available categories: {', '.join(sorted(available))}"
                )
            await ctx.enable_components(names=names)
            scope = f"'{category}'" + (f"/'{subcategory}'" if subcategory else "")
            return (
                f"Activated {len(names)} tools in {scope}"
                f": {', '.join(sorted(names))}"
            )

    # Expose prompts and resources as tools via transforms so that
    # tool-only clients can list/render prompts and list/read resources.
    mcp.add_transform(PromptsAsTools(mcp))
    mcp.add_transform(ResourcesAsTools(mcp))

    @mcp.tool(tags={"resource", "admin"})
    async def install_skill(
        skill_name: Annotated[
            str,
            Field(
                description=(
                    "Name of the skill (used as the directory name). "
                    "Must be a valid directory name (lowercase, underscores)."
                ),
            ),
        ],
        files: Annotated[
            dict[str, str],
            Field(
                description=(
                    "Dictionary of filename -> content for the skill directory. "
                    "Must include 'SKILL.md' as the main file. "
                    "May include supporting files such as templates, examples, "
                    "or configuration snippets (e.g. 'pyproject.toml.template', 'example.py')."
                ),
            ),
        ],
        target: Annotated[
            str,
            Field(
                description=(
                    "Target skills provider to install into. "
                    "Use 'bundled' for the server's built-in skills directory, "
                    "or a vendor name: "
                    + ", ".join(f"'{k}'" for k in _VENDOR_SKILLS_PROVIDERS)
                    + "."
                ),
            ),
        ] = "bundled",
    ) -> dict:
        """Install a skill (SKILL.md + supporting files) into a SkillsDirectoryProvider.

        Creates the skill directory if needed, writes all files,
        and registers the new skill with the target provider so it becomes
        immediately available via list_resources / read_resource.
        """
        if "SKILL.md" not in files:
            raise ValueError(
                "The 'files' dict must include a 'SKILL.md' entry as the main skill file."
            )

        # Find the target SkillsDirectoryProvider
        target_key = target.lower().strip()
        target_provider: SkillsDirectoryProvider | None = None

        for provider in mcp.providers:
            if not isinstance(provider, SkillsDirectoryProvider):
                continue

            if target_key == "bundled":
                if settings.default_skills_dir:
                    bundled_root = Path(settings.default_skills_dir).resolve()
                    if bundled_root in provider._roots:  # noqa: SLF001
                        target_provider = provider
                        break
            else:
                vendor_cls = _VENDOR_SKILLS_PROVIDERS.get(target_key)
                if vendor_cls and isinstance(provider, vendor_cls):
                    target_provider = provider
                    break

        if target_provider is None:
            available = ["bundled"]
            for p in mcp.providers:
                for vendor_name, vendor_cls in _VENDOR_SKILLS_PROVIDERS.items():
                    if isinstance(p, vendor_cls):
                        available.append(vendor_name)
            raise ValueError(
                f"Target provider '{target}' not found or not loaded. "
                f"Available targets: {', '.join(available)}"
            )

        if not target_provider._roots:  # noqa: SLF001
            raise ValueError(
                f"Target provider '{target}' has no configured root directories."
            )

        # Use the first root directory for writing
        root_dir = target_provider._roots[0]  # noqa: SLF001
        skill_dir = root_dir / skill_name

        # Create the directory and write all files
        skill_dir.mkdir(parents=True, exist_ok=True)
        written_files: list[str] = []
        for filename, content in files.items():
            file_path = skill_dir / filename
            # Create subdirectories if the filename contains path separators
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            written_files.append(filename)

        # Register the new skill with the provider
        already_loaded = {
            p._skill_path.name  # noqa: SLF001
            for p in target_provider.providers
            if hasattr(p, "_skill_path")
        }

        if skill_name not in already_loaded:
            new_skill_provider = SkillProvider(skill_path=skill_dir)
            target_provider.providers.append(new_skill_provider)
            action = "Installed"
        else:
            # Skill already exists — re-discover to pick up changed content
            target_provider._discover_skills()  # noqa: SLF001
            action = "Updated"

        logger.info(
            "%s skill '%s' (%d files) in %s provider (root: %s)",
            action,
            skill_name,
            len(written_files),
            target,
            root_dir,
        )

        return {
            "status": action.lower(),
            "skill_name": skill_name,
            "target": target,
            "path": str(skill_dir),
            "files_written": written_files,
            "uri": f"skill://{skill_name}/SKILL.md",
        }

    return mcp