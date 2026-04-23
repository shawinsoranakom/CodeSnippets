def _replay_wraps_for_command(self, cmd_name: str) -> None:
        """Recompose and rewrite agent files for a wrap-strategy command.

        Collects all installed presets that declare cmd_name in their
        wrap_commands registry field, sorts them so the highest-precedence
        preset (lowest priority number) wraps outermost, then writes the
        fully composed output to every agent directory.

        Called after every install and remove to keep agent files correct
        regardless of installation order.

        Args:
            cmd_name: Full command name (e.g. "speckit.specify")
        """
        try:
            from .agents import CommandRegistrar
        except ImportError:
            return

        # Collect enabled presets that wrap this command, sorted ascending
        # (lowest priority number = highest precedence = outermost).
        wrap_presets = []
        for pack_id, metadata in self.registry.list_by_priority(include_disabled=False):
            if cmd_name not in metadata.get("wrap_commands", []):
                continue
            pack_dir = self.presets_dir / pack_id
            if not pack_dir.is_dir():
                continue  # corrupted state — skip
            wrap_presets.append((pack_id, pack_dir))

        if not wrap_presets:
            return

        # Derive short name for core resolution fallback.
        short_name = cmd_name
        if short_name.startswith("speckit."):
            short_name = short_name[len("speckit."):]

        resolver = PresetResolver(self.project_root)
        core_file = (
            resolver.resolve_core(cmd_name, "command")
            or resolver.resolve_extension_command_via_manifest(cmd_name)
            or (
                resolver.resolve_extension_command_via_manifest(short_name)
                if short_name != cmd_name
                else None
            )
            or resolver.resolve_core(short_name, "command")
        )
        if core_file is None:
            return

        registrar = CommandRegistrar()
        core_frontmatter, core_body = registrar.parse_frontmatter(
            core_file.read_text(encoding="utf-8")
        )
        replay_aliases: List[str] = []
        seen_aliases: set[str] = set()

        # Apply wraps innermost-first (reverse of ascending list).
        accumulated_body = core_body
        outermost_frontmatter = {}
        outermost_pack_id = wrap_presets[0][0]  # fallback; updated per contributing preset
        for pack_id, pack_dir in reversed(wrap_presets):
            manifest_path = pack_dir / "preset.yml"
            cmd_file: Optional[Path] = None
            if manifest_path.exists():
                try:
                    manifest = PresetManifest(manifest_path)
                except (PresetValidationError, KeyError, TypeError, ValueError):
                    manifest = None
                if manifest is not None:
                    for template in manifest.templates:
                        if template.get("type") != "command" or template.get("name") != cmd_name:
                            continue
                        file_rel = template.get("file")
                        if isinstance(file_rel, str):
                            rel_path = Path(file_rel)
                            if not rel_path.is_absolute():
                                try:
                                    preset_root = pack_dir.resolve()
                                    candidate = (preset_root / rel_path).resolve()
                                    candidate.relative_to(preset_root)
                                except (OSError, ValueError):
                                    candidate = None
                                if candidate is not None:
                                    cmd_file = candidate
                        aliases = template.get("aliases", [])
                        if not isinstance(aliases, list):
                            aliases = []
                        for alias in aliases:
                            if isinstance(alias, str) and alias not in seen_aliases:
                                replay_aliases.append(alias)
                                seen_aliases.add(alias)
                        break
            if cmd_file is None:
                cmd_file = pack_dir / "commands" / f"{cmd_name}.md"
            if not cmd_file.exists():
                continue
            wrap_fm, wrap_body = registrar.parse_frontmatter(
                cmd_file.read_text(encoding="utf-8")
            )
            accumulated_body = wrap_body.replace("{CORE_TEMPLATE}", accumulated_body)
            outermost_frontmatter = wrap_fm  # last iteration = outermost preset
            outermost_pack_id = pack_id

        # Build final frontmatter: outermost preset wins; fall back to core for
        # scripts/agent_scripts if the outermost preset does not define them.
        final_frontmatter = dict(outermost_frontmatter)
        final_frontmatter.pop("strategy", None)
        for key in ("scripts", "agent_scripts"):
            if key not in final_frontmatter and key in core_frontmatter:
                final_frontmatter[key] = core_frontmatter[key]

        composed_content = (
            registrar.render_frontmatter(final_frontmatter) + "\n" + accumulated_body
        )

        self._replay_skill_override(cmd_name, composed_content, outermost_pack_id)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            cmd_dir = tmp_path / "commands"
            cmd_dir.mkdir()
            (cmd_dir / f"{cmd_name}.md").write_text(composed_content, encoding="utf-8")
            registrar._ensure_configs()
            for agent_name, agent_config in registrar.AGENT_CONFIGS.items():
                if agent_config.get("extension") == "/SKILL.md":
                    continue
                agent_dir = self.project_root / agent_config["dir"]
                if not agent_dir.exists():
                    continue
                try:
                    registrar.register_commands(
                        agent_name,
                        [{
                            "name": cmd_name,
                            "file": f"commands/{cmd_name}.md",
                            "aliases": replay_aliases,
                        }],
                        f"preset:{outermost_pack_id}",
                        tmp_path,
                        self.project_root,
                    )
                except ValueError:
                    continue