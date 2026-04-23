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