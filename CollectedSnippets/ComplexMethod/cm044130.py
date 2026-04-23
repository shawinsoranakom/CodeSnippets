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