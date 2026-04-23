def resolve_skill_placeholders(
        agent_name: str, frontmatter: dict, body: str, project_root: Path
    ) -> str:
        """Resolve script placeholders for skills-backed agents."""
        try:
            from . import load_init_options
        except ImportError:
            return body

        if not isinstance(frontmatter, dict):
            frontmatter = {}

        scripts = frontmatter.get("scripts", {}) or {}
        if not isinstance(scripts, dict):
            scripts = {}

        init_opts = load_init_options(project_root)
        if not isinstance(init_opts, dict):
            init_opts = {}

        script_variant = init_opts.get("script")
        if script_variant not in {"sh", "ps"}:
            fallback_order = []
            default_variant = (
                "ps" if platform.system().lower().startswith("win") else "sh"
            )
            secondary_variant = "sh" if default_variant == "ps" else "ps"

            if default_variant in scripts:
                fallback_order.append(default_variant)
            if secondary_variant in scripts:
                fallback_order.append(secondary_variant)

            for key in scripts:
                if key not in fallback_order:
                    fallback_order.append(key)

            script_variant = fallback_order[0] if fallback_order else None

        script_command = scripts.get(script_variant) if script_variant else None
        if script_command:
            script_command = script_command.replace("{ARGS}", "$ARGUMENTS")
            body = body.replace("{SCRIPT}", script_command)

        body = body.replace("{ARGS}", "$ARGUMENTS").replace("__AGENT__", agent_name)

        # Resolve __CONTEXT_FILE__ from init-options
        context_file = init_opts.get("context_file") or ""
        body = body.replace("__CONTEXT_FILE__", context_file)

        return CommandRegistrar.rewrite_project_relative_paths(body)