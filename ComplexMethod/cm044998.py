def process_template(
        content: str,
        agent_name: str,
        script_type: str,
        arg_placeholder: str = "$ARGUMENTS",
        context_file: str = "",
    ) -> str:
        """Process a raw command template into agent-ready content.

        Performs the same transformations as the release script:
        1. Extract ``scripts.<script_type>`` value from YAML frontmatter
        2. Replace ``{SCRIPT}`` with the extracted script command
        3. Strip ``scripts:`` section from frontmatter
        4. Replace ``{ARGS}`` and ``$ARGUMENTS`` with *arg_placeholder*
        5. Replace ``__AGENT__`` with *agent_name*
        6. Replace ``__CONTEXT_FILE__`` with *context_file*
        7. Rewrite paths: ``scripts/`` → ``.specify/scripts/`` etc.
        """
        # 1. Extract script command from frontmatter
        script_command = ""
        script_pattern = re.compile(
            rf"^\s*{re.escape(script_type)}:\s*(.+)$", re.MULTILINE
        )
        # Find the scripts: block
        in_scripts = False
        for line in content.splitlines():
            if line.strip() == "scripts:":
                in_scripts = True
                continue
            if in_scripts and line and not line[0].isspace():
                in_scripts = False
            if in_scripts:
                m = script_pattern.match(line)
                if m:
                    script_command = m.group(1).strip()
                    break

        # 2. Replace {SCRIPT}
        if script_command:
            content = content.replace("{SCRIPT}", script_command)

        # 3. Strip scripts: section from frontmatter
        lines = content.splitlines(keepends=True)
        output_lines: list[str] = []
        in_frontmatter = False
        skip_section = False
        dash_count = 0
        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped == "---":
                dash_count += 1
                if dash_count == 1:
                    in_frontmatter = True
                else:
                    in_frontmatter = False
                skip_section = False
                output_lines.append(line)
                continue
            if in_frontmatter:
                if stripped == "scripts:":
                    skip_section = True
                    continue
                if skip_section:
                    if line[0:1].isspace():
                        continue  # skip indented content under scripts
                    skip_section = False
            output_lines.append(line)
        content = "".join(output_lines)

        # 4. Replace {ARGS} and $ARGUMENTS
        content = content.replace("{ARGS}", arg_placeholder)
        content = content.replace("$ARGUMENTS", arg_placeholder)

        # 5. Replace __AGENT__
        content = content.replace("__AGENT__", agent_name)

        # 6. Replace __CONTEXT_FILE__
        content = content.replace("__CONTEXT_FILE__", context_file)

        # 7. Rewrite paths — delegate to the shared implementation in
        #    CommandRegistrar so extension-local paths are preserved and
        #    boundary rules stay consistent across the codebase.
        from specify_cli.agents import CommandRegistrar

        content = CommandRegistrar.rewrite_project_relative_paths(content)

        return content