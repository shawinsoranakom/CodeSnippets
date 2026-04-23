def render_yaml_command(
        self,
        frontmatter: dict,
        body: str,
        source_id: str,
        cmd_name: str = "",
    ) -> str:
        """Render command in YAML recipe format for Goose.

        Args:
            frontmatter: Command frontmatter
            body: Command body content
            source_id: Source identifier (extension or preset ID)
            cmd_name: Command name used as title fallback

        Returns:
            Formatted YAML recipe file content
        """
        from specify_cli.integrations.base import YamlIntegration

        title = frontmatter.get("title", "") or frontmatter.get("name", "")
        if not isinstance(title, str):
            title = str(title) if title is not None else ""
        if not title and cmd_name:
            title = YamlIntegration._human_title(cmd_name)
        if not title and source_id:
            title = YamlIntegration._human_title(Path(str(source_id)).stem)
        if not title:
            title = "Command"

        description = frontmatter.get("description", "")
        if not isinstance(description, str):
            description = str(description) if description is not None else ""
        return YamlIntegration._render_yaml(title, description, body, source_id)