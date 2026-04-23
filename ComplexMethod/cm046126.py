def render_jinja_macros() -> None:
    """Render MiniJinja macros in Markdown files before building with MkDocs."""
    mkdocs_yml = DOCS.parent / "mkdocs.yml"
    default_yaml = DOCS.parent / "ultralytics" / "cfg" / "default.yaml"

    class SafeFallbackLoader(yaml.SafeLoader):
        """SafeLoader that gracefully skips unknown tags (required for mkdocs.yml)."""

    def _ignore_unknown(loader, tag_suffix, node):
        """Gracefully handle YAML tags that aren't registered."""
        if isinstance(node, yaml.ScalarNode):
            return loader.construct_scalar(node)
        if isinstance(node, yaml.SequenceNode):
            return loader.construct_sequence(node)
        if isinstance(node, yaml.MappingNode):
            return loader.construct_mapping(node)
        return None

    SafeFallbackLoader.add_multi_constructor("", _ignore_unknown)

    def load_yaml(path: Path, *, safe_loader: yaml.Loader = yaml.SafeLoader) -> dict:
        """Load YAML safely, returning an empty dict on errors."""
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                return yaml.load(f, Loader=safe_loader) or {}
        except Exception as e:
            LOGGER.warning(f"Could not load {path}: {e}")
            return {}

    mkdocs_cfg = load_yaml(mkdocs_yml, safe_loader=SafeFallbackLoader)
    extra_vars = mkdocs_cfg.get("extra", {}) or {}
    site_name = mkdocs_cfg.get("site_name", "Ultralytics Docs")
    extra_vars.update(load_yaml(default_yaml))

    env = Environment(
        loader=load_from_path([DOCS / "en", DOCS]),
        auto_escape_callback=lambda _: False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )

    def indent_filter(value: str, width: int = 4, first: bool = False, blank: bool = False) -> str:
        """Mimic Jinja's indent filter to preserve macros compatibility."""
        prefix = " " * int(width)
        result = []
        for i, line in enumerate(str(value).splitlines(keepends=True)):
            if not line.strip() and not blank:
                result.append(line)
                continue
            if i == 0 and not first:
                result.append(line)
            else:
                result.append(prefix + line)
        return "".join(result)

    env.add_filter("indent", indent_filter)
    reserved_keys = {"name"}
    base_context = {**extra_vars, "page": {"meta": {}}, "config": {"site_name": site_name}}

    files_processed = 0
    files_with_macros = 0
    macros_total = 0

    pbar = TQDM((DOCS / "en").rglob("*.md"), desc="MiniJinja: 0 macros, 0 pages")
    for md_file in pbar:
        if "macros" in md_file.parts or "reference" in md_file.parts:
            continue
        files_processed += 1

        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception as e:
            LOGGER.warning(f"Could not read {md_file}: {e}")
            continue
        if "{{" not in content and "{%" not in content:
            continue

        parts = content.split("---\n")
        frontmatter = ""
        frontmatter_data = {}
        markdown_content = content
        if content.startswith("---\n") and len(parts) >= 3:
            frontmatter = f"---\n{parts[1]}---\n"
            markdown_content = "---\n".join(parts[2:])
            try:
                frontmatter_data = yaml.safe_load(parts[1]) or {}
            except Exception as e:
                LOGGER.warning(f"Could not parse frontmatter in {md_file}: {e}")

        macro_hits = markdown_content.count("{{") + markdown_content.count("{%")
        if not macro_hits:
            continue

        context = {k: v for k, v in base_context.items() if k not in reserved_keys}
        context.update({k: v for k, v in frontmatter_data.items() if k not in reserved_keys})
        context["page"] = context.get("page", {})
        context["page"]["meta"] = frontmatter_data

        try:
            rendered = env.render_str(markdown_content, name=str(md_file.relative_to(DOCS)), **context)
        except Exception as e:
            LOGGER.warning(f"Error rendering macros in {md_file}: {e}")
            continue

        md_file.write_text(frontmatter + rendered, encoding="utf-8")
        files_with_macros += 1
        macros_total += macro_hits
        pbar.set_description(f"MiniJinja: {macros_total} macros, {files_with_macros} pages")