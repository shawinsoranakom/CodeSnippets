def test_extension_skill_restored_on_preset_remove(self, project_dir, temp_dir):
        """Preset removal should restore an extension-backed skill instead of deleting it."""
        self._write_init_options(project_dir, ai="codex")
        skills_dir = project_dir / ".agents" / "skills"
        self._create_skill(skills_dir, "speckit-fakeext-cmd", body="original extension skill")

        extension_dir = project_dir / ".specify" / "extensions" / "fakeext"
        (extension_dir / "commands").mkdir(parents=True, exist_ok=True)
        (extension_dir / "commands" / "cmd.md").write_text(
            "---\n"
            "description: Extension fakeext cmd\n"
            "scripts:\n"
            "  sh: ../../scripts/bash/setup-plan.sh --json \"{ARGS}\"\n"
            "---\n\n"
            "extension:fakeext\n"
            "Run {SCRIPT}\n"
        )
        extension_manifest = {
            "schema_version": "1.0",
            "extension": {
                "id": "fakeext",
                "name": "Fake Extension",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "commands": [
                    {
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/cmd.md",
                        "description": "Fake extension command",
                    }
                ]
            },
        }
        with open(extension_dir / "extension.yml", "w") as f:
            yaml.dump(extension_manifest, f)

        preset_dir = temp_dir / "ext-skill-restore"
        preset_dir.mkdir()
        (preset_dir / "commands").mkdir()
        (preset_dir / "commands" / "speckit.fakeext.cmd.md").write_text(
            "---\ndescription: Override fakeext cmd\n---\n\npreset:ext-skill-restore\n"
        )
        preset_manifest = {
            "schema_version": "1.0",
            "preset": {
                "id": "ext-skill-restore",
                "name": "Ext Skill Restore",
                "version": "1.0.0",
                "description": "Test",
            },
            "requires": {"speckit_version": ">=0.1.0"},
            "provides": {
                "templates": [
                    {
                        "type": "command",
                        "name": "speckit.fakeext.cmd",
                        "file": "commands/speckit.fakeext.cmd.md",
                    }
                ]
            },
        }
        with open(preset_dir / "preset.yml", "w") as f:
            yaml.dump(preset_manifest, f)

        manager = PresetManager(project_dir)
        manager.install_from_directory(preset_dir, "0.1.5")

        skill_file = skills_dir / "speckit-fakeext-cmd" / "SKILL.md"
        assert "preset:ext-skill-restore" in skill_file.read_text()

        manager.remove("ext-skill-restore")

        assert skill_file.exists()
        content = skill_file.read_text()
        assert "preset:ext-skill-restore" not in content
        assert "source: extension:fakeext" in content
        assert "extension:fakeext" in content
        assert '.specify/scripts/bash/setup-plan.sh --json "$ARGUMENTS"' in content
        assert "# Fakeext Cmd Skill" in content