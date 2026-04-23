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