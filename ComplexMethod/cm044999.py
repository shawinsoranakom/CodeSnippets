def _extract_frontmatter(content: str) -> dict[str, Any]:
        """Extract frontmatter as a dict from YAML frontmatter block."""
        import yaml

        if not content.startswith("---"):
            return {}

        lines = content.splitlines(keepends=True)
        if not lines or lines[0].rstrip("\r\n") != "---":
            return {}

        frontmatter_end = -1
        for i, line in enumerate(lines[1:], start=1):
            if line.rstrip("\r\n") == "---":
                frontmatter_end = i
                break

        if frontmatter_end == -1:
            return {}

        frontmatter_text = "".join(lines[1:frontmatter_end])
        try:
            fm = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            return {}

        return fm if isinstance(fm, dict) else {}