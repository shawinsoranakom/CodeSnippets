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